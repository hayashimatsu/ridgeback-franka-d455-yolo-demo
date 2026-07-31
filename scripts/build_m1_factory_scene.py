"""Author the M1 factory shelf as a clean sublayer of the candidate scene.

Run this file inside the connected Isaac Sim Kit process.  It never saves the
active baseline root layer.  Instead, it builds a separate content layer and
exports a new candidate root from a clean anonymous snapshot of the baseline on
disk.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import omni.timeline
import omni.usd
from pxr import Gf, Sdf, Semantics, Usd, UsdGeom


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = PROJECT_ROOT / "scenes/ridgeback_franka_d455_demo.usd"
CANDIDATE_PATH = PROJECT_ROOT / "scenes/ridgeback_franka_d455_yolo_demo.usd"
CONTENT_PATH = PROJECT_ROOT / "scenes/m1_factory_content.usda"
CATALOG_PATH = PROJECT_ROOT / "config/object_catalog.yaml"
RESULT_PATH = Path("/tmp/m1_step2_build.json")
TEMP_CANDIDATE_PATH = PROJECT_ROOT / "scenes/.m1_step2_candidate.tmp.usd"
TEMP_CONTENT_PATH = PROJECT_ROOT / "scenes/.m1_factory_content.tmp.usda"
TEMP_CATALOG_PATH = PROJECT_ROOT / "config/.object_catalog.tmp.yaml"
EXPECTED_BASELINE_SHA256 = (
    "a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _set_xform(
    xformable: UsdGeom.Xformable,
    translate: tuple[float, float, float],
    rotate_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0),
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> None:
    xformable.ClearXformOpOrder()
    xformable.AddTranslateOp().Set(Gf.Vec3d(*translate))
    xformable.AddRotateXYZOp().Set(Gf.Vec3f(*rotate_xyz))
    xformable.AddScaleOp().Set(Gf.Vec3f(*scale))


def _cube(
    stage: Usd.Stage,
    path: str,
    translate: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    color: tuple[float, float, float],
) -> UsdGeom.Cube:
    cube = UsdGeom.Cube.Define(stage, path)
    cube.CreateSizeAttr(1.0)
    cube.CreateExtentAttr([Gf.Vec3f(-0.5), Gf.Vec3f(0.5)])
    cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    _set_xform(cube, translate, scale=dimensions)
    return cube


def _apply_semantics(prim: Usd.Prim, class_name: str) -> None:
    api = Semantics.SemanticsAPI.Apply(prim, "Semantics")
    api.CreateSemanticTypeAttr().Set("class")
    api.CreateSemanticDataAttr().Set(class_name)


def _reference_asset(
    stage: Usd.Stage,
    path: str,
    asset: dict[str, object],
    translate: tuple[float, float, float],
    rotate_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> Usd.Prim:
    xform = UsdGeom.Xform.Define(stage, path)
    _set_xform(xform, translate, rotate_xyz)
    reference_path = "../" + str(asset["usd_reference_path"])
    xform.GetPrim().GetReferences().AddReference(reference_path)
    prim = xform.GetPrim()
    _apply_semantics(prim, str(asset["semantic_label"]))
    prim.CreateAttribute("catalog:assetId", Sdf.ValueTypeNames.String).Set(
        str(asset["asset_id"])
    )
    prim.CreateAttribute("catalog:split", Sdf.ValueTypeNames.String).Set(
        str(asset["split"])
    )
    return prim


def _build_content(catalog: dict[str, object]) -> dict[str, object]:
    if TEMP_CONTENT_PATH.exists():
        TEMP_CONTENT_PATH.unlink()
    stage = Usd.Stage.CreateNew(str(TEMP_CONTENT_PATH))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    factory = UsdGeom.Xform.Define(stage, "/World/Factory")
    factory.GetPrim().CreateAttribute("factory:sceneVersion", Sdf.ValueTypeNames.String).Set(
        "m1-step2-v1"
    )

    # A low three-tier rack fits the baseline D455's downward-looking view while
    # retaining recognizable factory shelving and a clear backstop.
    rack_color = (0.20, 0.24, 0.28)
    shelf_color = (0.34, 0.38, 0.42)
    _cube(stage, "/World/Factory/Rack/BackPanel", (1.66, 0.0, 0.50), (0.035, 1.28, 1.00), rack_color)
    for index, z_value in enumerate((0.06, 0.34, 0.62, 0.90)):
        _cube(
            stage,
            f"/World/Factory/Rack/Shelf_{index}",
            (1.39, 0.0, z_value),
            (0.56, 1.28, 0.035),
            shelf_color,
        )
    for y_value, name in ((-0.61, "Left"), (0.61, "Right")):
        _cube(
            stage,
            f"/World/Factory/Rack/Post_{name}_Front",
            (1.12, y_value, 0.49),
            (0.045, 0.045, 0.98),
            rack_color,
        )
        _cube(
            stage,
            f"/World/Factory/Rack/Post_{name}_Back",
            (1.65, y_value, 0.49),
            (0.045, 0.045, 0.98),
            rack_color,
        )

    # Factory-zone floor markings provide hard negatives without physics.
    for index, y_value in enumerate((-0.75, 0.75)):
        _cube(
            stage,
            f"/World/Factory/FloorMarking_{index}",
            (1.40, y_value, 0.012),
            (0.90, 0.045, 0.018),
            (0.92, 0.66, 0.05),
        )

    assets = list(catalog["assets"])
    by_class: dict[str, list[dict[str, object]]] = {}
    for asset in assets:
        by_class.setdefault(str(asset["class_name"]), []).append(asset)

    library = UsdGeom.Xform.Define(stage, "/World/Factory/ObjectLibrary")
    UsdGeom.Imageable(library.GetPrim()).CreateVisibilityAttr().Set(
        UsdGeom.Tokens.invisible
    )
    for class_name, class_assets in sorted(by_class.items()):
        UsdGeom.Xform.Define(stage, f"/World/Factory/ObjectLibrary/{class_name}")
        for asset in class_assets:
            _reference_asset(
                stage,
                f"/World/Factory/ObjectLibrary/{class_name}/{asset['asset_id']}",
                asset,
                (0.0, 0.0, 0.0),
            )

    # Four identities per class (three train, one validation) are displayed.
    # Held-out identities remain in the hidden library only.
    selected_by_class: dict[str, list[dict[str, object]]] = {}
    for class_name in ("box", "bottle", "hand_tool", "ball", "mechanical_part"):
        class_assets = by_class[class_name]
        train_assets = [asset for asset in class_assets if asset["split"] == "train"]
        validation_assets = [
            asset for asset in class_assets if asset["split"] == "validation"
        ]
        selected_by_class[class_name] = train_assets[:3] + validation_assets[:1]
    selected = [
        selected_by_class[class_name][variant_index]
        for variant_index in range(4)
        for class_name in ("box", "bottle", "hand_tool", "ball", "mechanical_part")
    ]

    placements = [
        # bottom shelf: seven objects
        (1.30, -0.51, 0.08, (0.0, 0.0, 0.0)),
        (1.44, -0.35, 0.08, (0.0, 0.0, 15.0)),
        (1.27, -0.18, 0.08, (0.0, 0.0, -12.0)),
        (1.45, 0.00, 0.08, (0.0, 0.0, 8.0)),
        (1.27, 0.18, 0.08, (0.0, 0.0, -8.0)),
        (1.44, 0.35, 0.08, (0.0, 0.0, 12.0)),
        (1.30, 0.51, 0.08, (0.0, 0.0, 0.0)),
        # middle shelf: seven objects
        (1.30, -0.51, 0.36, (0.0, 0.0, 5.0)),
        (1.44, -0.35, 0.36, (0.0, 0.0, -12.0)),
        (1.27, -0.18, 0.36, (0.0, 0.0, 10.0)),
        (1.45, 0.00, 0.36, (0.0, 0.0, -6.0)),
        (1.27, 0.18, 0.36, (0.0, 0.0, 14.0)),
        (1.44, 0.35, 0.36, (0.0, 0.0, -10.0)),
        (1.30, 0.51, 0.36, (0.0, 0.0, 3.0)),
        # upper shelf: six objects
        (1.31, -0.48, 0.64, (0.0, 0.0, -8.0)),
        (1.44, -0.29, 0.64, (0.0, 0.0, 10.0)),
        (1.28, -0.10, 0.64, (0.0, 0.0, -5.0)),
        (1.44, 0.10, 0.64, (0.0, 0.0, 7.0)),
        (1.28, 0.29, 0.64, (0.0, 0.0, -11.0)),
        (1.42, 0.48, 0.64, (0.0, 0.0, 4.0)),
    ]
    display_root = UsdGeom.Xform.Define(stage, "/World/Factory/DisplayObjects")
    display_root.GetPrim().CreateAttribute(
        "factory:maximumConfiguredObjects", Sdf.ValueTypeNames.Int
    ).Set(20)
    display_counts: dict[str, int] = {}
    for display_index, (asset, placement) in enumerate(
        zip(selected, placements, strict=True)
    ):
        x_value, y_value, shelf_z, rotation = placement
        object_height = float(asset["geometry"]["nominal_dimensions_m"][2])
        z_value = (
            shelf_z
            if asset["class_name"] == "bottle"
            else shelf_z + object_height * 0.5
        )
        prim = _reference_asset(
            stage,
            f"/World/Factory/DisplayObjects/{asset['asset_id']}",
            asset,
            (x_value, y_value, z_value),
            rotation,
        )
        prim.CreateAttribute("factory:displayIndex", Sdf.ValueTypeNames.Int).Set(
            display_index
        )
        class_name = str(asset["class_name"])
        display_counts[class_name] = display_counts.get(class_name, 0) + 1

    stage.GetRootLayer().Save()
    stage = None
    normalized_content = TEMP_CONTENT_PATH.read_text(encoding="utf-8").rstrip() + "\n"
    TEMP_CONTENT_PATH.write_text(normalized_content, encoding="utf-8")
    os.replace(TEMP_CONTENT_PATH, CONTENT_PATH)
    return {
        "content_path": str(CONTENT_PATH),
        "content_sha256": _sha256(CONTENT_PATH),
        "library_asset_count": len(assets),
        "display_object_count": len(selected),
        "display_counts": display_counts,
    }


def _validate_composed_candidate(stage: Usd.Stage) -> None:
    factory = stage.GetPrimAtPath("/World/Factory")
    if not factory.IsValid():
        raise RuntimeError("candidate stage does not compose /World/Factory")
    library = stage.GetPrimAtPath("/World/Factory/ObjectLibrary")
    visibility = UsdGeom.Imageable(library).GetVisibilityAttr().Get()
    if visibility != UsdGeom.Tokens.invisible:
        raise RuntimeError("object library is not hidden")
    library_assets = [
        asset_prim
        for class_prim in library.GetChildren()
        for asset_prim in class_prim.GetChildren()
    ]
    if len(library_assets) != 30:
        raise RuntimeError(f"expected 30 library assets, got {len(library_assets)}")

    display_root = stage.GetPrimAtPath("/World/Factory/DisplayObjects")
    display_prims = list(display_root.GetChildren())
    if len(display_prims) != 20:
        raise RuntimeError(f"expected 20 display objects, got {len(display_prims)}")
    class_counts: dict[str, int] = {}
    indices = []
    for prim in display_prims:
        if not list(prim.GetChildren()):
            raise RuntimeError(f"unresolved asset reference at {prim.GetPath()}")
        api = Semantics.SemanticsAPI(prim, "Semantics")
        if api.GetSemanticTypeAttr().Get() != "class":
            raise RuntimeError(f"invalid semantic type at {prim.GetPath()}")
        class_name = api.GetSemanticDataAttr().Get()
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
        indices.append(prim.GetAttribute("factory:displayIndex").Get())
    expected_counts = {
        "box": 4,
        "bottle": 4,
        "hand_tool": 4,
        "ball": 4,
        "mechanical_part": 4,
    }
    if class_counts != expected_counts:
        raise RuntimeError(f"display class counts mismatch: {class_counts}")
    if sorted(indices) != list(range(20)):
        raise RuntimeError(f"display indices mismatch: {sorted(indices)}")


def build_factory_scene() -> dict[str, object]:
    timeline = omni.timeline.get_timeline_interface()
    active_stage = omni.usd.get_context().get_stage()
    active_root = active_stage.GetRootLayer()
    active_path = Path(os.path.abspath(active_root.realPath or active_root.identifier))
    baseline_before = _sha256(BASELINE_PATH)
    result: dict[str, object] = {
        "schema": "m1-step2-factory-build-v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "active_stage_before": str(active_path),
        "active_root_dirty_before": bool(active_root.dirty),
        "timeline_playing_before": timeline.is_playing(),
        "baseline_sha256_before": baseline_before,
        "failures": [],
    }
    try:
        if timeline.is_playing():
            raise RuntimeError("timeline must be stopped before factory authoring")
        if active_path != BASELINE_PATH:
            raise RuntimeError(f"unexpected pre-authoring active stage: {active_path}")
        if baseline_before != EXPECTED_BASELINE_SHA256:
            raise RuntimeError(f"protected baseline hash mismatch: {baseline_before}")

        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        content_result = _build_content(catalog)

        clean_baseline = Sdf.Layer.OpenAsAnonymous(str(BASELINE_PATH))
        if clean_baseline is None:
            raise RuntimeError("could not open clean anonymous baseline layer")
        clean_baseline.subLayerPaths.append(CONTENT_PATH.name)
        TEMP_CANDIDATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if TEMP_CANDIDATE_PATH.exists():
            TEMP_CANDIDATE_PATH.unlink()
        if not clean_baseline.Export(str(TEMP_CANDIDATE_PATH)):
            raise RuntimeError("could not export candidate root layer")

        candidate_stage = Usd.Stage.Open(str(TEMP_CANDIDATE_PATH), Usd.Stage.LoadAll)
        if candidate_stage is None:
            raise RuntimeError("candidate stage could not be opened after export")
        _validate_composed_candidate(candidate_stage)
        if _sha256(BASELINE_PATH) != baseline_before:
            raise RuntimeError("protected baseline changed before candidate replace")
        candidate_stage = None
        os.replace(TEMP_CANDIDATE_PATH, CANDIDATE_PATH)

        candidate_sha = _sha256(CANDIDATE_PATH)
        baseline_after = _sha256(BASELINE_PATH)
        if baseline_after != baseline_before:
            raise RuntimeError("protected baseline changed during candidate build")

        catalog["scene_lineage"]["candidate_step2_sha256"] = candidate_sha
        catalog["scene_lineage"]["factory_content_path"] = (
            "scenes/m1_factory_content.usda"
        )
        catalog["scene_lineage"]["factory_content_sha256"] = content_result[
            "content_sha256"
        ]
        catalog["scene_lineage"]["step2_authored_at_utc"] = result[
            "timestamp_utc"
        ]
        TEMP_CATALOG_PATH.write_text(
            json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(TEMP_CATALOG_PATH, CATALOG_PATH)

        result.update(content_result)
        result.update(
            {
                "candidate_path": str(CANDIDATE_PATH),
                "candidate_sha256": candidate_sha,
                "baseline_sha256_after": baseline_after,
                "catalog_sha256_after": _sha256(CATALOG_PATH),
                "status": "pass",
            }
        )
    except Exception as error:
        result["failures"].append(repr(error))
        result["status"] = "fail"
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build_factory_scene(), indent=2))
