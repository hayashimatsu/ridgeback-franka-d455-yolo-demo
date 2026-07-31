"""Build the immutable M1-S3 correction revision inside Isaac Sim Kit.

The reviewed candidate is an input and is never saved or overwritten.  The
new revision restores the D455 left camera's asset-local transform and authors
the runtime-solved Panda pose that matches the user's reviewed IK target.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

from pxr import Gf, Sdf, Usd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "scenes/ridgeback_franka_d455_yolo_demo.usd"
DESTINATION = PROJECT_ROOT / "scenes/ridgeback_franka_d455_yolo_demo_m1_r3.usd"
TEMP_DESTINATION = DESTINATION.with_name(
    f".{DESTINATION.stem}.tmp{DESTINATION.suffix}"
)
RESULT = PROJECT_ROOT / "validation/tmp/codex_m1_revision_build.json"

EXPECTED_SOURCE_SHA256 = (
    "05329ddde64616b1bc05287520002e3c862942572225006232bfa76ee0b01758"
)
LEFT_CAMERA = (
    "/World/ridgeback_franka/panda_hand/d455_camera/RSD455/"
    "Camera_OmniVision_OV9782_Left"
)
IK_TARGET = "/World/IKTarget"

# The original user-reviewed target remains unchanged. The arm pose was solved
# against it at runtime and directly reviewed through capture 8.
IK_TARGET_POSITION_M = (0.1579919159412384, -0.04624408110976219, 0.8840093016624451)
IK_TARGET_ORIENTATION_WXYZ = (
    -0.008186659775674445,
    0.8174175124037867,
    0.005015881327810696,
    0.5759656499756112,
)
SOLVED_ARM_POSE_RAD = (
    0.01729314960539341,
    -1.8316730260849,
    0.00927724689245224,
    -2.999994993209839,
    0.012023942545056343,
    2.3971686363220215,
    0.7912395596504211,
)
LEFT_CAMERA_TRANSLATE_M = (0.0, -0.0475, 0.0)
REVISION_AUTHORED_AT_UTC = "2026-07-31T06:15:12.023693+00:00"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build() -> dict[str, object]:
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    source_hash = _sha256(SOURCE)
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"reviewed candidate hash mismatch: {source_hash}")
    if DESTINATION.exists():
        raise FileExistsError(f"refusing to overwrite revision: {DESTINATION}")
    if TEMP_DESTINATION.exists():
        raise FileExistsError(f"stale temporary revision exists: {TEMP_DESTINATION}")

    source_layer = Sdf.Layer.FindOrOpen(str(SOURCE))
    if source_layer is None or not source_layer.Export(str(TEMP_DESTINATION)):
        raise RuntimeError("could not export reviewed candidate to temporary revision")

    try:
        stage = Usd.Stage.Open(str(TEMP_DESTINATION), Usd.Stage.LoadNone)
        if stage is None:
            raise RuntimeError("could not open temporary revision")
        stage.SetEditTarget(stage.GetRootLayer())

        left = stage.GetPrimAtPath(LEFT_CAMERA)
        target = stage.GetPrimAtPath(IK_TARGET)
        if not left.IsValid() or not target.IsValid():
            raise RuntimeError("required left camera or IKTarget prim is missing")

        left_translate = left.GetAttribute("xformOp:translate")
        target_translate = target.GetAttribute("xformOp:translate")
        target_orient = target.GetAttribute("xformOp:orient")
        if not all((left_translate.IsValid(), target_translate.IsValid(), target_orient.IsValid())):
            raise RuntimeError("required authored xform attributes are missing")

        left_translate.Set(Gf.Vec3d(*LEFT_CAMERA_TRANSLATE_M))
        target_translate.Set(Gf.Vec3d(*IK_TARGET_POSITION_M))
        w, x, y, z = IK_TARGET_ORIENTATION_WXYZ
        target_orient.Set(Gf.Quatd(w, Gf.Vec3d(x, y, z)))

        for index, position_rad in enumerate(SOLVED_ARM_POSE_RAD, start=1):
            joint = stage.GetPrimAtPath(
                f"/World/ridgeback_franka/panda_link{index - 1}/panda_joint{index}"
            )
            if not joint.IsValid():
                raise RuntimeError(f"missing Panda joint {index}")
            position_deg = math.degrees(position_rad)
            for name in (
                "drive:angular:physics:targetPosition",
                "state:angular:physics:position",
            ):
                attribute = joint.GetAttribute(name)
                if not attribute.IsValid():
                    raise RuntimeError(f"panda_joint{index} missing {name}")
                attribute.Set(position_deg)

        layer = stage.GetRootLayer()
        custom = dict(layer.customLayerData)
        custom["m1_revision"] = {
            "purpose": "restore D455 left camera and align Panda with reviewed IKTarget",
            "source_scene": SOURCE.name,
            "source_sha256": source_hash,
            "authored_at_utc": REVISION_AUTHORED_AT_UTC,
        }
        custom["demo_clean_arm_pose_rad"] = json.dumps(list(SOLVED_ARM_POSE_RAD))
        layer.customLayerData = custom
        layer.Save()

        verify_stage = Usd.Stage.Open(str(TEMP_DESTINATION), Usd.Stage.LoadNone)
        observed_left = tuple(
            verify_stage.GetPrimAtPath(LEFT_CAMERA).GetAttribute("xformOp:translate").Get()
        )
        observed_target = tuple(
            verify_stage.GetPrimAtPath(IK_TARGET).GetAttribute("xformOp:translate").Get()
        )
        if observed_left != LEFT_CAMERA_TRANSLATE_M:
            raise RuntimeError(f"left camera verification failed: {observed_left}")
        if max(abs(a - b) for a, b in zip(observed_target, IK_TARGET_POSITION_M)) > 1e-12:
            raise RuntimeError(f"IKTarget verification failed: {observed_target}")

        os.replace(TEMP_DESTINATION, DESTINATION)
    except Exception:
        if TEMP_DESTINATION.exists():
            TEMP_DESTINATION.unlink()
        raise

    result = {
        "schema": "m1-s3-revision-build-v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "source": SOURCE.relative_to(PROJECT_ROOT).as_posix(),
        "source_sha256": source_hash,
        "destination": DESTINATION.relative_to(PROJECT_ROOT).as_posix(),
        "destination_sha256": _sha256(DESTINATION),
        "left_camera_translate_m": list(LEFT_CAMERA_TRANSLATE_M),
        "ik_target_position_m": list(IK_TARGET_POSITION_M),
        "ik_target_orientation_wxyz": list(IK_TARGET_ORIENTATION_WXYZ),
        "solved_arm_pose_rad": list(SOLVED_ARM_POSE_RAD),
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
