"""Validate the authored M1 factory scene inside the active Isaac Sim Kit."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import omni.timeline
import omni.usd
from pxr import Semantics, Usd, UsdPhysics


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = PROJECT_ROOT / "scenes/ridgeback_franka_d455_demo.usd"
CANDIDATE_PATH = PROJECT_ROOT / "scenes/ridgeback_franka_d455_yolo_demo.usd"
CONTENT_PATH = PROJECT_ROOT / "scenes/m1_factory_content.usda"
CATALOG_PATH = PROJECT_ROOT / "config/object_catalog.yaml"
RESULT_PATH = Path("/tmp/m1_step2_validation.json")
EXPECTED_BASELINE_SHA256 = (
    "a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc"
)
EXPECTED_CLASSES = {"box", "bottle", "hand_tool", "ball", "mechanical_part"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_m1_step2() -> dict[str, object]:
    stage = omni.usd.get_context().get_stage()
    root = stage.GetRootLayer()
    active_path = Path(os.path.abspath(root.realPath or root.identifier))
    timeline = omni.timeline.get_timeline_interface()
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []

    if active_path != CANDIDATE_PATH:
        failures.append(f"active stage is not the candidate: {active_path}")
    baseline_sha = _sha256(BASELINE_PATH)
    candidate_sha = _sha256(CANDIDATE_PATH)
    content_sha = _sha256(CONTENT_PATH)
    if baseline_sha != EXPECTED_BASELINE_SHA256:
        failures.append(f"protected baseline hash mismatch: {baseline_sha}")
    lineage = catalog["scene_lineage"]
    if candidate_sha != lineage.get("candidate_step2_sha256"):
        failures.append("candidate Step2 hash does not match catalog lineage")
    if content_sha != lineage.get("factory_content_sha256"):
        failures.append("factory content hash does not match catalog lineage")
    if CONTENT_PATH.name not in root.subLayerPaths:
        failures.append("candidate root does not include the factory content sublayer")

    required_prims = [
        "/World/ridgeback_franka",
        "/World/ridgeback_franka/panda_hand",
        "/World/IKTarget",
        "/World/Factory",
        "/World/Factory/Rack",
        "/World/Factory/ObjectLibrary",
        "/World/Factory/DisplayObjects",
    ]
    missing_prims = [path for path in required_prims if not stage.GetPrimAtPath(path).IsValid()]
    failures.extend(f"missing required prim: {path}" for path in missing_prims)

    display_root = stage.GetPrimAtPath("/World/Factory/DisplayObjects")
    display_prims = list(display_root.GetChildren()) if display_root.IsValid() else []
    if len(display_prims) != 20:
        failures.append(f"expected 20 display objects, got {len(display_prims)}")
    configured = display_root.GetAttribute("factory:maximumConfiguredObjects")
    if not configured.IsValid() or configured.Get() != 20:
        failures.append("maximum configured object count is not 20")

    class_counts: Counter[str] = Counter()
    asset_ids: list[str] = []
    semantic_failures: list[str] = []
    for prim in display_prims:
        asset_id_attr = prim.GetAttribute("catalog:assetId")
        split_attr = prim.GetAttribute("catalog:split")
        asset_id = asset_id_attr.Get() if asset_id_attr.IsValid() else None
        split = split_attr.Get() if split_attr.IsValid() else None
        if not asset_id:
            failures.append(f"{prim.GetPath()}: missing catalog asset id")
        else:
            asset_ids.append(asset_id)
        if split not in {"train", "validation"}:
            failures.append(f"{prim.GetPath()}: invalid displayed split {split}")

        api = Semantics.SemanticsAPI(prim, "Semantics")
        semantic_type = api.GetSemanticTypeAttr().Get()
        semantic_data = api.GetSemanticDataAttr().Get()
        if semantic_type != "class" or semantic_data not in EXPECTED_CLASSES:
            semantic_failures.append(str(prim.GetPath()))
        else:
            class_counts[str(semantic_data)] += 1
        if not list(prim.GetChildren()):
            failures.append(f"{prim.GetPath()}: referenced asset did not compose children")

    if len(asset_ids) != len(set(asset_ids)):
        failures.append("displayed asset identities are not unique")
    if semantic_failures:
        failures.append(f"invalid semantics on: {semantic_failures}")
    if class_counts != Counter({class_name: 4 for class_name in EXPECTED_CLASSES}):
        failures.append(f"display class counts mismatch: {dict(class_counts)}")

    library_root = stage.GetPrimAtPath("/World/Factory/ObjectLibrary")
    library_assets = []
    if library_root.IsValid():
        for class_prim in library_root.GetChildren():
            library_assets.extend(list(class_prim.GetChildren()))
    if len(library_assets) != 30:
        failures.append(f"expected 30 library assets, got {len(library_assets)}")

    factory_root = stage.GetPrimAtPath("/World/Factory")
    rigid_body_prims = [
        str(prim.GetPath())
        for prim in Usd.PrimRange(factory_root)
        if prim.HasAPI(UsdPhysics.RigidBodyAPI)
    ]
    if rigid_body_prims:
        failures.append(f"unexpected factory rigid bodies: {rigid_body_prims}")

    result = {
        "schema": "m1-step2-validation-v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not failures else "fail",
        "active_stage": str(active_path),
        "root_dirty": bool(root.dirty),
        "timeline_playing": timeline.is_playing(),
        "baseline_sha256": baseline_sha,
        "candidate_sha256": candidate_sha,
        "factory_content_sha256": content_sha,
        "display_object_count": len(display_prims),
        "display_class_counts": dict(sorted(class_counts.items())),
        "library_asset_count": len(library_assets),
        "factory_rigid_body_count": len(rigid_body_prims),
        "missing_prims": missing_prims,
        "failures": failures,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(validate_m1_step2(), indent=2))
