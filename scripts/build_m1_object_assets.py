"""Build the project-authored M1 proxy assets and object catalog.

The generated catalog is JSON syntax stored in a ``.yaml`` file. JSON is a
strict subset of YAML 1.2, which keeps the file dependency-free and directly
readable by both JSON and YAML tooling.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_SCENE = PROJECT_ROOT / "scenes/ridgeback_franka_d455_demo.usd"
CANDIDATE_SCENE = PROJECT_ROOT / "scenes/ridgeback_franka_d455_yolo_demo.usd"
ASSET_ROOT = PROJECT_ROOT / "assets/objects"
CATALOG_PATH = PROJECT_ROOT / "config/object_catalog.yaml"
PARENT_COMMIT = "439015e93fa47ffea75de0329d41c3dba61ab220"
EXPECTED_BASELINE_SHA256 = (
    "a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc"
)


@dataclass(frozen=True)
class Part:
    name: str
    primitive: str
    dimensions_m: tuple[float, float, float]
    translate_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotate_xyz_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class Asset:
    asset_id: str
    class_id: int
    class_name: str
    display_name: str
    split: str
    nominal_dimensions_m: tuple[float, float, float]
    scale_range: tuple[float, float]
    color_rgb: tuple[float, float, float]
    parts: tuple[Part, ...]


def _box_assets() -> list[Asset]:
    rows = [
        ("box_small_carton", "Small carton", "train", (0.18, 0.14, 0.12), (0.75, 1.30), (0.72, 0.46, 0.24)),
        ("box_tall_parcel", "Tall parcel", "train", (0.14, 0.13, 0.28), (0.75, 1.20), (0.82, 0.68, 0.32)),
        ("box_flat_package", "Flat package", "train", (0.30, 0.22, 0.07), (0.80, 1.20), (0.34, 0.58, 0.78)),
        ("box_cube_carton", "Cube carton", "validation", (0.19, 0.19, 0.19), (0.75, 1.25), (0.74, 0.30, 0.25)),
        ("box_wide_crate", "Wide crate", "validation", (0.34, 0.18, 0.15), (0.75, 1.15), (0.28, 0.55, 0.34)),
        ("box_long_case", "Long case", "held_out", (0.42, 0.12, 0.10), (0.80, 1.15), (0.22, 0.24, 0.29)),
    ]
    assets = []
    for asset_id, display, split, dims, scale_range, color in rows:
        assets.append(
            Asset(
                asset_id, 0, "box", display, split, dims, scale_range, color,
                (
                    Part("Body", "Cube", dims),
                    Part("TopBand", "Cube", (dims[0] * 0.08, dims[1] * 1.01, dims[2] * 1.01)),
                ),
            )
        )
    return assets


def _bottle_assets() -> list[Asset]:
    rows = [
        ("bottle_short_amber", "Short amber bottle", "train", 0.075, 0.18, (0.55, 0.22, 0.08)),
        ("bottle_tall_blue", "Tall blue bottle", "train", 0.065, 0.27, (0.12, 0.35, 0.72)),
        ("bottle_wide_green", "Wide green bottle", "train", 0.10, 0.22, (0.12, 0.58, 0.30)),
        ("bottle_slim_white", "Slim white bottle", "validation", 0.052, 0.24, (0.86, 0.86, 0.82)),
        ("bottle_square_red", "Square red bottle", "validation", 0.082, 0.20, (0.68, 0.12, 0.12)),
        ("bottle_flask_violet", "Violet flask bottle", "held_out", 0.095, 0.19, (0.46, 0.18, 0.62)),
    ]
    assets = []
    for index, (asset_id, display, split, diameter, height, color) in enumerate(rows):
        body_kind = "Cube" if "square" in asset_id else ("Sphere" if "flask" in asset_id else "Cylinder")
        body_height = height * (0.66 if "flask" in asset_id else 0.72)
        assets.append(
            Asset(
                asset_id, 1, "bottle", display, split,
                (diameter, diameter, height), (0.80, 1.20), color,
                (
                    Part("Body", body_kind, (diameter, diameter, body_height), (0.0, 0.0, body_height / 2.0)),
                    Part("Neck", "Cylinder", (diameter * 0.42, diameter * 0.42, height * 0.20), (0.0, 0.0, body_height + height * 0.10)),
                    Part("Cap", "Cylinder", (diameter * 0.50, diameter * 0.50, height * 0.08), (0.0, 0.0, body_height + height * 0.24)),
                ),
            )
        )
    return assets


def _tool_assets() -> list[Asset]:
    specs = [
        Asset("hand_tool_hammer", 2, "hand_tool", "Claw hammer", "train", (0.28, 0.10, 0.04), (0.80, 1.20), (0.72, 0.18, 0.12), (
            Part("Handle", "Cylinder", (0.035, 0.035, 0.24), (0.0, 0.0, 0.0), (0.0, 90.0, 0.0)),
            Part("Head", "Cube", (0.10, 0.04, 0.045), (0.12, 0.0, 0.0)),
        )),
        Asset("hand_tool_wrench", 2, "hand_tool", "Open-end wrench", "train", (0.26, 0.07, 0.025), (0.80, 1.20), (0.48, 0.50, 0.54), (
            Part("Shaft", "Cube", (0.20, 0.025, 0.018)),
            Part("JawA", "Cube", (0.065, 0.018, 0.025), (0.105, 0.024, 0.0), (0.0, 0.0, 28.0)),
            Part("JawB", "Cube", (0.065, 0.018, 0.025), (0.105, -0.024, 0.0), (0.0, 0.0, -28.0)),
        )),
        Asset("hand_tool_screwdriver", 2, "hand_tool", "Screwdriver", "train", (0.30, 0.055, 0.055), (0.80, 1.20), (0.92, 0.55, 0.08), (
            Part("Grip", "Cylinder", (0.055, 0.055, 0.12), (-0.09, 0.0, 0.0), (0.0, 90.0, 0.0)),
            Part("Shaft", "Cylinder", (0.012, 0.012, 0.18), (0.06, 0.0, 0.0), (0.0, 90.0, 0.0)),
        )),
        Asset("hand_tool_pliers", 2, "hand_tool", "Combination pliers", "validation", (0.24, 0.10, 0.035), (0.80, 1.15), (0.15, 0.38, 0.72), (
            Part("HandleA", "Cube", (0.18, 0.025, 0.025), (-0.03, 0.025, 0.0), (0.0, 0.0, 10.0)),
            Part("HandleB", "Cube", (0.18, 0.025, 0.025), (-0.03, -0.025, 0.0), (0.0, 0.0, -10.0)),
            Part("Jaw", "Cone", (0.08, 0.07, 0.035), (0.09, 0.0, 0.0), (0.0, 90.0, 0.0)),
        )),
        Asset("hand_tool_mallet", 2, "hand_tool", "Rubber mallet", "validation", (0.30, 0.12, 0.07), (0.80, 1.15), (0.18, 0.18, 0.20), (
            Part("Handle", "Cylinder", (0.04, 0.04, 0.25), (0.0, 0.0, 0.0), (0.0, 90.0, 0.0)),
            Part("Head", "Cylinder", (0.12, 0.12, 0.11), (0.11, 0.0, 0.0), (90.0, 0.0, 0.0)),
        )),
        Asset("hand_tool_hex_key", 2, "hand_tool", "L-shaped hex key", "held_out", (0.22, 0.12, 0.018), (0.85, 1.20), (0.32, 0.33, 0.36), (
            Part("LongArm", "Cylinder", (0.018, 0.018, 0.22), (0.0, 0.0, 0.0), (0.0, 90.0, 0.0)),
            Part("ShortArm", "Cylinder", (0.018, 0.018, 0.12), (-0.105, 0.055, 0.0), (90.0, 0.0, 0.0)),
        )),
    ]
    return specs


def _ball_assets() -> list[Asset]:
    rows = [
        ("ball_red_small", "Small red ball", "train", (0.09, 0.09, 0.09), (0.12, 0.12, 0.75)),
        ("ball_blue_medium", "Medium blue ball", "train", (0.14, 0.14, 0.14), (0.12, 0.32, 0.82)),
        ("ball_green_large", "Large green ball", "train", (0.20, 0.20, 0.20), (0.12, 0.62, 0.28)),
        ("ball_orange_oval", "Orange oval ball", "validation", (0.18, 0.13, 0.13), (0.94, 0.42, 0.08)),
        ("ball_white_flattened", "White flattened ball", "validation", (0.16, 0.16, 0.11), (0.88, 0.88, 0.84)),
        ("ball_violet_rugby", "Violet rugby ball", "held_out", (0.22, 0.12, 0.12), (0.52, 0.17, 0.66)),
    ]
    return [
        Asset(asset_id, 3, "ball", display, split, dims, (0.80, 1.20), color, (Part("Body", "Sphere", dims),))
        for asset_id, display, split, dims, color in rows
    ]


def _mechanical_assets() -> list[Asset]:
    return [
        Asset("mechanical_part_flange", 4, "mechanical_part", "Four-lug flange", "train", (0.18, 0.18, 0.045), (0.80, 1.20), (0.38, 0.40, 0.43), (
            Part("Hub", "Cylinder", (0.13, 0.13, 0.045)),
            Part("LugX", "Cube", (0.18, 0.045, 0.03)),
            Part("LugY", "Cube", (0.045, 0.18, 0.03)),
        )),
        Asset("mechanical_part_pulley", 4, "mechanical_part", "Stepped pulley", "train", (0.14, 0.14, 0.08), (0.80, 1.20), (0.20, 0.25, 0.30), (
            Part("Outer", "Cylinder", (0.14, 0.14, 0.045)),
            Part("Inner", "Cylinder", (0.09, 0.09, 0.08)),
        )),
        Asset("mechanical_part_coupling", 4, "mechanical_part", "Shaft coupling", "train", (0.09, 0.09, 0.15), (0.80, 1.20), (0.64, 0.30, 0.08), (
            Part("Body", "Cylinder", (0.09, 0.09, 0.15)),
            Part("Band", "Cylinder", (0.105, 0.105, 0.035)),
        )),
        Asset("mechanical_part_bracket", 4, "mechanical_part", "L bracket", "validation", (0.16, 0.12, 0.12), (0.80, 1.20), (0.26, 0.32, 0.42), (
            Part("Base", "Cube", (0.16, 0.12, 0.025), (0.0, 0.0, -0.0475)),
            Part("Upright", "Cube", (0.025, 0.12, 0.12), (-0.0675, 0.0, 0.0)),
        )),
        Asset("mechanical_part_housing", 4, "mechanical_part", "Machine housing", "validation", (0.19, 0.14, 0.11), (0.80, 1.15), (0.38, 0.18, 0.15), (
            Part("Body", "Cube", (0.19, 0.14, 0.08)),
            Part("Boss", "Cylinder", (0.08, 0.08, 0.06), (0.0, 0.0, 0.065)),
        )),
        Asset("mechanical_part_roller", 4, "mechanical_part", "Industrial roller", "held_out", (0.22, 0.10, 0.10), (0.80, 1.15), (0.16, 0.44, 0.48), (
            Part("Roll", "Cylinder", (0.10, 0.10, 0.18), (0.0, 0.0, 0.0), (0.0, 90.0, 0.0)),
            Part("Axle", "Cylinder", (0.035, 0.035, 0.22), (0.0, 0.0, 0.0), (0.0, 90.0, 0.0)),
        )),
    ]


def _all_assets() -> list[Asset]:
    return _box_assets() + _bottle_assets() + _tool_assets() + _ball_assets() + _mechanical_assets()


def _tuple(values: tuple[float, float, float]) -> str:
    return "(" + ", ".join(f"{value:.6g}" for value in values) + ")"


def _part_usda(part: Part, color: tuple[float, float, float]) -> str:
    extent = {
        "Cube": "[(-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)]",
        "Sphere": "[(-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)]",
        "Cylinder": "[(-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)]",
        "Capsule": "[(-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)]",
        "Cone": "[(-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)]",
    }[part.primitive]
    geometry = {
        "Cube": "        double size = 1\n",
        "Sphere": "        double radius = 0.5\n",
        "Cylinder": "        uniform token axis = \"Z\"\n        double height = 1\n        double radius = 0.5\n",
        "Capsule": "        uniform token axis = \"Z\"\n        double height = 0.5\n        double radius = 0.25\n",
        "Cone": "        uniform token axis = \"Z\"\n        double height = 1\n        double radius = 0.5\n",
    }[part.primitive]
    return (
        f'    def {part.primitive} "{part.name}"\n'
        "    {\n"
        f"        float3[] extent = {extent}\n"
        + geometry
        + f"        color3f[] primvars:displayColor = [{_tuple(color)}]\n"
        + "        uniform token primvars:displayColor:interpolation = \"constant\"\n"
        + f"        double3 xformOp:translate = {_tuple(part.translate_m)}\n"
        + f"        double3 xformOp:rotateXYZ = {_tuple(part.rotate_xyz_deg)}\n"
        + f"        double3 xformOp:scale = {_tuple(part.dimensions_m)}\n"
        + '        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]\n'
        + "    }\n"
    )


def _asset_usda(asset: Asset) -> str:
    parts = "\n".join(_part_usda(part, asset.color_rgb) for part in asset.parts)
    return (
        "#usda 1.0\n"
        "(\n"
        '    defaultPrim = "Asset"\n'
        "    metersPerUnit = 1\n"
        '    upAxis = "Z"\n'
        ")\n\n"
        'def Xform "Asset"\n'
        "{\n"
        f'    custom string catalog:assetId = "{asset.asset_id}"\n'
        f'    custom string catalog:className = "{asset.class_name}"\n'
        f'    custom string catalog:semanticLabel = "{asset.class_name}"\n\n'
        f"{parts}\n"
        "}\n"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build() -> dict[str, object]:
    baseline_sha = _sha256(BASELINE_SCENE)
    if baseline_sha != EXPECTED_BASELINE_SHA256:
        raise RuntimeError(f"protected baseline hash mismatch: {baseline_sha}")
    if not CANDIDATE_SCENE.is_file():
        raise RuntimeError(f"candidate scene is missing: {CANDIDATE_SCENE}")

    assets = _all_assets()
    if len(assets) != 30:
        raise RuntimeError(f"expected 30 assets, got {len(assets)}")

    catalog_assets = []
    for asset in assets:
        relative_path = Path("assets/objects") / asset.class_name / f"{asset.asset_id}.usda"
        output_path = PROJECT_ROOT / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_asset_usda(asset), encoding="utf-8")
        catalog_assets.append(
            {
                "asset_id": asset.asset_id,
                "class_id": asset.class_id,
                "class_name": asset.class_name,
                "semantic_label": asset.class_name,
                "display_name": asset.display_name,
                "usd_reference_path": relative_path.as_posix(),
                "default_prim_path": "/Asset",
                "planned_scene_prim_path": f"/World/Factory/ObjectLibrary/{asset.class_name}/{asset.asset_id}",
                "asset_sha256": _sha256(output_path),
                "source": {
                    "provider": "project_authored",
                    "generator": "scripts/build_m1_object_assets.py",
                    "generator_version": 1,
                    "external_asset": False,
                },
                "license": {
                    "identifier": "NOASSERTION",
                    "terms_record": "Repository has no LICENSE file as of the parent commit.",
                    "use_conditions": "Project use authorized by the M1 implementation request; independent redistribution requires repository-owner approval.",
                    "redistribution_allowed": False,
                },
                "geometry": {
                    "nominal_dimensions_m": list(asset.nominal_dimensions_m),
                    "uniform_scale_range": list(asset.scale_range),
                },
                "split": asset.split,
                "availability": "available",
                "limitations": [
                    "Procedural proxy asset with intentionally simple geometry and materials.",
                    "No standalone redistribution license has been declared by the repository owner.",
                ],
            }
        )

    taxonomy = [
        {"class_id": 0, "name": "box", "semantic_label": "box"},
        {"class_id": 1, "name": "bottle", "semantic_label": "bottle"},
        {"class_id": 2, "name": "hand_tool", "semantic_label": "hand_tool"},
        {"class_id": 3, "name": "ball", "semantic_label": "ball"},
        {"class_id": 4, "name": "mechanical_part", "semantic_label": "mechanical_part"},
    ]
    catalog = {
        "schema_version": 1,
        "format_note": "JSON syntax; valid YAML 1.2",
        "catalog_id": "ridgeback_franka_d455_yolo_m1_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scene_lineage": {
            "parent_commit": PARENT_COMMIT,
            "parent_scene_path": "scenes/ridgeback_franka_d455_demo.usd",
            "parent_scene_sha256": baseline_sha,
            "candidate_scene_path": "scenes/ridgeback_franka_d455_yolo_demo.usd",
            "candidate_initial_sha256": _sha256(CANDIDATE_SCENE),
        },
        "taxonomy": taxonomy,
        "assets": catalog_assets,
        "validation_rules": {
            "minimum_assets_per_class": 6,
            "required_splits": ["train", "validation", "held_out"],
            "identity_overlap_allowed": False,
            "maximum_scene_instances": 20,
        },
        "catalog_limitations": [
            "The assets are project-authored procedural proxies, not external SimReady assets.",
            "The repository has no LICENSE file; redistribution_allowed is therefore false for every asset until the owner supplies terms.",
            "Scene placement, semantic API authoring, and visual acceptance are deferred to M1-Step2 and M1-Step3.",
        ],
    }
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    return {
        "catalog": CATALOG_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "asset_count": len(catalog_assets),
        "baseline_sha256": baseline_sha,
        "candidate_initial_sha256": _sha256(CANDIDATE_SCENE),
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
