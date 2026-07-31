"""Run the repeatable M0 clean-reopen baseline checks inside Isaac Sim."""

from __future__ import annotations

import hashlib
import json
import os
import traceback

import numpy as np

import omni.kit.app
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import Articulation, XformPrim


ARTICULATION_PATH = "/World/ridgeback_franka"
HAND_PATH = "/World/ridgeback_franka/panda_hand"
LEFT_CAMERA_PATH = (
    "/World/ridgeback_franka/panda_hand/d455_camera/RSD455/"
    "Camera_OmniVision_OV9782_Left"
)
TARGET_PATH = "/World/IKTarget"
POSE_OFFSETS_M = (
    np.array([-0.04, 0.04, -0.02], dtype=np.float32),
    np.array([-0.02, -0.03, -0.005], dtype=np.float32),
)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_script(path, namespace):
    with open(path, "r", encoding="utf-8") as source:
        exec(compile(source.read(), path, "exec"), namespace)


def _quat_to_matrix(quaternion):
    w, x, y, z = np.asarray(quaternion, dtype=np.float64)
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def _relative_camera_pose(hand, camera):
    hand_position, hand_quaternion = hand.get_world_poses()
    camera_position, camera_quaternion = camera.get_world_poses()
    hand_position = hand_position.numpy()[0].astype(np.float64)
    hand_quaternion = hand_quaternion.numpy()[0].astype(np.float64)
    camera_position = camera_position.numpy()[0].astype(np.float64)
    camera_quaternion = camera_quaternion.numpy()[0].astype(np.float64)
    hand_rotation = _quat_to_matrix(hand_quaternion)
    camera_rotation = _quat_to_matrix(camera_quaternion)
    return {
        "translation_m": (
            hand_rotation.T @ (camera_position - hand_position)
        ).tolist(),
        "rotation_matrix": (hand_rotation.T @ camera_rotation).tolist(),
    }


def _wait_for_target(controller, app, maximum_frames=240, stable_frames=5):
    stable = 0
    last_status = None
    for frame in range(1, maximum_frames + 1):
        app.update()
        last_status = controller.status()
        error = last_status.get("last_error")
        if isinstance(error, dict):
            within_tolerance = (
                error.get("pos_error_norm", float("inf")) <= 0.002
                and error.get("rot_error_norm", float("inf")) <= 0.01
            )
            stable = stable + 1 if within_tolerance else 0
            if stable >= stable_frames:
                return {
                    "settled": True,
                    "frames": frame,
                    "status": last_status,
                }
        else:
            stable = 0
    return {
        "settled": False,
        "frames": maximum_frames,
        "status": last_status,
    }


def run_baseline_acceptance():
    context = omni.usd.get_context()
    stage = context.get_stage()
    root = stage.GetRootLayer()
    stage_path = os.path.abspath(root.realPath or root.identifier)
    project_root = os.path.dirname(os.path.dirname(stage_path))
    output_path = os.path.join(
        project_root, "validation", "tmp", "clean_reopen_runtime.json"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    app = omni.kit.app.get_app()
    timeline = omni.timeline.get_timeline_interface()
    result = {
        "schema": "ridgeback-d455-baseline-runtime-v1",
        "stage_path": stage_path,
        "stage_sha256_before": _sha256(stage_path),
        "root_dirty_before": bool(root.dirty),
        "failures": [],
    }
    namespace = globals()

    try:
        timeline.stop()
        for _ in range(5):
            app.update()
        timeline.play()
        for _ in range(10):
            app.update()

        articulation = Articulation(ARTICULATION_PATH)
        dof_names = list(articulation.dof_names)
        arm_dof_indices = [
            dof_names.index(f"panda_joint{index}") for index in range(1, 8)
        ]
        non_arm_dof_indices = [
            index for index in range(len(dof_names)) if index not in arm_dof_indices
        ]
        play_positions_before = articulation.get_dof_positions().numpy()[0].copy()
        for _ in range(120):
            app.update()
        play_positions_after = articulation.get_dof_positions().numpy()[0].copy()
        play_drift = np.abs(play_positions_after - play_positions_before)
        result["play_stability"] = {
            "frames": 120,
            "arm_dof_names": [dof_names[index] for index in arm_dof_indices],
            "max_abs_arm_joint_delta_rad": float(
                np.max(play_drift[arm_dof_indices])
            ),
            "max_abs_non_arm_dof_delta_rad_or_m": float(
                np.max(play_drift[non_arm_dof_indices])
            ),
        }

        _load_script(os.path.join(project_root, "scripts", "ik_controller.py"), namespace)
        _load_script(os.path.join(project_root, "scripts", "capture_d455.py"), namespace)

        first_start = namespace["ik_follow_start"]()
        second_start = namespace["ik_follow_start"]()
        capture_setup = namespace["demo_capture_setup"]()
        subscription_count = namespace["ik_follow_subscription_count"]()
        result["startup"] = {
            "first": first_start,
            "second": second_start,
            "subscription_count": subscription_count,
            "capture_setup": capture_setup,
        }

        import builtins

        controller = getattr(builtins, "_ik_follow_controller_registry")["instance"]
        target = XformPrim(TARGET_PATH)
        hand = XformPrim(HAND_PATH)
        camera = XformPrim(LEFT_CAMERA_PATH)
        target_position, target_quaternion = target.get_world_poses()
        target_position = target_position.numpy()[0].astype(np.float32)
        target_quaternion = target_quaternion.numpy()[0].astype(np.float32)

        poses = []
        captures = []
        for index, offset in enumerate(POSE_OFFSETS_M, start=1):
            target.set_world_poses(
                np.asarray([target_position + offset], dtype=np.float32),
                np.asarray([target_quaternion], dtype=np.float32),
            )
            settle = _wait_for_target(controller, app)
            relative_pose = _relative_camera_pose(hand, camera)
            capture = namespace["demo_capture"]()
            poses.append(
                {
                    "index": index,
                    "target_offset_m": offset.tolist(),
                    "settle": settle,
                    "hand_to_left_camera": relative_pose,
                }
            )
            captures.append(capture)

        result["poses"] = poses
        result["captures"] = captures
        if len(poses) == 2:
            translation_1 = np.asarray(
                poses[0]["hand_to_left_camera"]["translation_m"]
            )
            translation_2 = np.asarray(
                poses[1]["hand_to_left_camera"]["translation_m"]
            )
            rotation_1 = np.asarray(
                poses[0]["hand_to_left_camera"]["rotation_matrix"]
            )
            rotation_2 = np.asarray(
                poses[1]["hand_to_left_camera"]["rotation_matrix"]
            )
            result["attachment"] = {
                "translation_delta_m": float(
                    np.linalg.norm(translation_2 - translation_1)
                ),
                "max_rotation_matrix_element_delta": float(
                    np.max(np.abs(rotation_2 - rotation_1))
                ),
            }

        if result["play_stability"]["max_abs_arm_joint_delta_rad"] > 1e-4:
            result["failures"].append(
                "Play stability Panda arm joint drift exceeded 1e-4 rad"
            )
        if subscription_count != 1:
            result["failures"].append("IK subscription count is not exactly one")
        if any(not pose["settle"]["settled"] for pose in poses):
            result["failures"].append("one or more IK poses did not settle")
        if result["attachment"]["translation_delta_m"] > 2e-6:
            result["failures"].append("D455 relative translation drift exceeded 2e-6 m")
        if result["attachment"]["max_rotation_matrix_element_delta"] > 2e-5:
            result["failures"].append("D455 relative rotation drift exceeded 2e-5")
        if any(capture.get("status") != "pass" for capture in captures):
            result["failures"].append("one or more captures failed")
        capture_directories = [capture.get("output_directory") for capture in captures]
        if len(set(capture_directories)) != len(capture_directories):
            result["failures"].append("capture directories are not unique")
    except Exception as error:
        result["failures"].append(f"runtime exception: {error!r}")
        result["traceback"] = traceback.format_exc()
    finally:
        try:
            if "ik_follow_stop" in namespace:
                result["stop"] = namespace["ik_follow_stop"]()
        except Exception as stop_error:
            result["failures"].append(f"stop exception: {stop_error!r}")
        timeline.stop()
        for _ in range(10):
            app.update()
        result["subscription_count_after_stop"] = (
            namespace["ik_follow_subscription_count"]()
            if "ik_follow_subscription_count" in namespace
            else None
        )
        result["timeline_playing_after_stop"] = timeline.is_playing()
        result["stage_sha256_after"] = _sha256(stage_path)
        result["root_dirty_after"] = bool(stage.GetRootLayer().dirty)
        if result["stage_sha256_after"] != result["stage_sha256_before"]:
            result["failures"].append("root USD changed during runtime acceptance")
        if result["subscription_count_after_stop"] not in (0, None):
            result["failures"].append("IK subscription remained after stop")
        if result["timeline_playing_after_stop"]:
            result["failures"].append("timeline remained playing after stop")
        result["status"] = "pass" if not result["failures"] else "fail"
        with open(output_path, "w", encoding="utf-8") as output:
            json.dump(result, output, indent=2)

    return result


BASELINE_ACCEPTANCE_RESULT = run_baseline_acceptance()
