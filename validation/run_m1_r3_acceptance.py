"""Run the exact-hash public M1-R3 operator workflow inside Isaac Sim Kit."""

from __future__ import annotations

import builtins
import hashlib
import json
import math
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import omni.kit.app
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import XformPrim
from pxr import UsdGeom


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENE = PROJECT_ROOT / "scenes/ridgeback_franka_d455_yolo_demo_m1_r3.usd"
RESULT = PROJECT_ROOT / "validation/tmp/codex_m1_r3_public_workflow.json"
EXPECTED_SCENE_SHA256 = (
    "092f9d445a9580946621601e4f918799e1959b9ad80302e1cbb9df67adfd6106"
)
REGISTRY_ATTR = "_ik_follow_controller_registry"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict[str, object]:
    result: dict[str, object] = {
        "schema": "m1-r3-public-workflow-v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "probe": "codex_m1_r3_public_workflow",
    }
    timeline = omni.timeline.get_timeline_interface()
    namespace: dict[str, object] = {}
    try:
        stage = omni.usd.get_context().get_stage()
        layer = stage.GetRootLayer()
        active_path = Path(layer.realPath or layer.identifier).resolve()
        scene_hash_before = _sha256(SCENE)
        if active_path != SCENE.resolve():
            raise RuntimeError(f"active stage is not M1-R3: {active_path}")
        if scene_hash_before != EXPECTED_SCENE_SHA256:
            raise RuntimeError(f"M1-R3 hash mismatch: {scene_hash_before}")
        if timeline.is_playing():
            raise RuntimeError("timeline must be stopped before public workflow")

        cache = UsdGeom.XformCache()
        target_matrix = cache.GetLocalToWorldTransform(stage.GetPrimAtPath("/World/IKTarget"))
        hand_matrix = cache.GetLocalToWorldTransform(
            stage.GetPrimAtPath("/World/ridgeback_franka/panda_hand")
        )
        pre_target_position = np.asarray(target_matrix.ExtractTranslation(), dtype=float)
        pre_hand_position = np.asarray(hand_matrix.ExtractTranslation(), dtype=float)
        pre_target_quat_obj = target_matrix.ExtractRotationQuat()
        pre_target_quat = np.asarray(
            [pre_target_quat_obj.GetReal(), *pre_target_quat_obj.GetImaginary()],
            dtype=float,
        )

        authored_degrees: list[float] = []
        for index in range(1, 8):
            joint = stage.GetPrimAtPath(
                f"/World/ridgeback_franka/panda_link{index - 1}/panda_joint{index}"
            )
            authored_degrees.append(
                float(joint.GetAttribute("state:angular:physics:position").Get())
            )

        demo_path = PROJECT_ROOT / "scripts/demo_start.py"
        exec(
            compile(demo_path.read_text(encoding="utf-8"), str(demo_path), "exec"),
            namespace,
        )
        for _ in range(60):
            omni.kit.app.get_app().update()

        registry = getattr(builtins, REGISTRY_ATTR, {})
        controller = registry.get("instance") if isinstance(registry, dict) else None
        if controller is None:
            raise RuntimeError("public demo_start did not register an IK controller")
        all_positions = controller._art.get_dof_positions().numpy()[0]
        runtime_positions = np.asarray(
            [all_positions[index] for index in controller._arm_dof_indices], dtype=float
        )

        target = XformPrim("/World/IKTarget")
        hand = XformPrim("/World/ridgeback_franka/panda_hand")
        post_target_position, post_target_quat = target.get_world_poses()
        post_hand_position, _ = hand.get_world_poses()
        target_position = post_target_position.numpy()[0]
        target_quat = post_target_quat.numpy()[0]
        hand_position = post_hand_position.numpy()[0]
        quat_dot = min(1.0, abs(float(np.dot(pre_target_quat, target_quat))))

        result.update(
            {
                "active_stage": str(active_path),
                "root_dirty": bool(layer.dirty),
                "scene_sha256_before": scene_hash_before,
                "pre_target_pos_m": pre_target_position.tolist(),
                "pre_hand_pos_m": pre_hand_position.tolist(),
                "authored_joint_positions_deg": authored_degrees,
                "runtime_joint_positions_rad": runtime_positions.tolist(),
                "configured_clean_pose_rad": controller._clean_arm_targets.tolist(),
                "max_joint_startup_delta_rad": float(
                    np.max(np.abs(runtime_positions - np.radians(authored_degrees)))
                ),
                "target_startup_translation_delta_m": float(
                    np.linalg.norm(target_position - pre_target_position)
                ),
                "target_startup_orientation_delta_rad": float(2.0 * math.acos(quat_dot)),
                "target_to_hand_after_start_m": float(
                    np.linalg.norm(target_position - hand_position)
                ),
                "demo_start_result": namespace["DEMO_START_RESULT"],
                "ik_status": namespace["ik_follow_status"](),
                "subscription_count_running": namespace[
                    "ik_follow_subscription_count"
                ](),
            }
        )

        result["capture_result"] = namespace["demo_capture"]()
        result["capture_status"] = namespace["demo_capture_status"]()
        result["demo_stop_result"] = namespace["demo_stop"]()
        timeline.stop()
        for _ in range(5):
            omni.kit.app.get_app().update()
        result.update(
            {
                "subscription_count_after_stop": namespace[
                    "ik_follow_subscription_count"
                ](),
                "timeline_is_playing_after": bool(timeline.is_playing()),
                "scene_sha256_after": _sha256(SCENE),
                "status": "ok",
            }
        )
    except Exception as exc:
        result.update(
            {"status": "error", "error": repr(exc), "traceback": traceback.format_exc()}
        )
    finally:
        try:
            count = namespace.get("ik_follow_subscription_count")
            if callable(count) and count():
                namespace["demo_stop"]()
        except Exception:
            result["cleanup_error"] = traceback.format_exc()
        timeline.stop()
        for _ in range(5):
            omni.kit.app.get_app().update()
        result["timeline_is_playing_finally"] = bool(timeline.is_playing())
        RESULT.parent.mkdir(parents=True, exist_ok=True)
        RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
