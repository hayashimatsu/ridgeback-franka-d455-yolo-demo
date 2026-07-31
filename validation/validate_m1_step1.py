"""Validate the M1-Step1 catalog, proxy assets, and scene lineage."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PROJECT_ROOT / "config/object_catalog.yaml"
EXPECTED_CLASSES = {
    0: "box",
    1: "bottle",
    2: "hand_tool",
    3: "ball",
    4: "mechanical_part",
}
EXPECTED_BASELINE_SHA256 = (
    "a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc"
)
REQUIRED_SPLITS = {"train", "validation", "held_out"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate() -> dict[str, object]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []
    usd_parse_status = "not_run_pxr_unavailable"

    taxonomy = {row["class_id"]: row["name"] for row in catalog["taxonomy"]}
    if taxonomy != EXPECTED_CLASSES:
        failures.append(f"taxonomy mismatch: {taxonomy}")

    assets = catalog["assets"]
    asset_ids = [asset["asset_id"] for asset in assets]
    reference_paths = [asset["usd_reference_path"] for asset in assets]
    if len(asset_ids) != len(set(asset_ids)):
        failures.append("asset_id values are not globally unique")
    if len(reference_paths) != len(set(reference_paths)):
        failures.append("usd_reference_path values are not unique")

    counts = Counter(asset["class_name"] for asset in assets)
    splits: dict[str, set[str]] = defaultdict(set)
    split_asset_ids: dict[str, set[str]] = defaultdict(set)
    for asset in assets:
        asset_id = asset["asset_id"]
        class_id = asset["class_id"]
        class_name = asset["class_name"]
        split = asset["split"]
        if EXPECTED_CLASSES.get(class_id) != class_name:
            failures.append(f"{asset_id}: class id/name mismatch")
        if asset["semantic_label"] != class_name:
            failures.append(f"{asset_id}: semantic label mismatch")
        if split not in REQUIRED_SPLITS:
            failures.append(f"{asset_id}: invalid split {split}")
        splits[class_name].add(split)
        split_asset_ids[split].add(asset_id)
        if asset["availability"] != "available":
            failures.append(f"{asset_id}: asset is not available")

        license_record = asset.get("license", {})
        for key in ("identifier", "terms_record", "use_conditions", "redistribution_allowed"):
            if key not in license_record:
                failures.append(f"{asset_id}: missing license.{key}")
        if license_record.get("redistribution_allowed") is not False:
            failures.append(f"{asset_id}: redistribution must remain false without owner terms")

        dimensions = asset["geometry"]["nominal_dimensions_m"]
        scale_range = asset["geometry"]["uniform_scale_range"]
        if len(dimensions) != 3 or any(value <= 0 for value in dimensions):
            failures.append(f"{asset_id}: invalid nominal dimensions")
        if len(scale_range) != 2 or not 0 < scale_range[0] <= scale_range[1]:
            failures.append(f"{asset_id}: invalid scale range")

        asset_path = PROJECT_ROOT / asset["usd_reference_path"]
        if not asset_path.is_file():
            failures.append(f"{asset_id}: missing USD file {asset_path}")
        elif _sha256(asset_path) != asset["asset_sha256"]:
            failures.append(f"{asset_id}: USD hash mismatch")
        else:
            header = asset_path.read_text(encoding="utf-8").splitlines()[0]
            if header != "#usda 1.0":
                failures.append(f"{asset_id}: invalid USDA header")

    for class_name in EXPECTED_CLASSES.values():
        if counts[class_name] < 6:
            failures.append(f"{class_name}: only {counts[class_name]} assets")
        if splits[class_name] != REQUIRED_SPLITS:
            failures.append(f"{class_name}: split coverage is {sorted(splits[class_name])}")

    split_names = sorted(split_asset_ids)
    for index, left in enumerate(split_names):
        for right in split_names[index + 1 :]:
            overlap = split_asset_ids[left] & split_asset_ids[right]
            if overlap:
                failures.append(f"identity overlap between {left} and {right}: {sorted(overlap)}")

    lineage = catalog["scene_lineage"]
    baseline_path = PROJECT_ROOT / lineage["parent_scene_path"]
    candidate_path = PROJECT_ROOT / lineage["candidate_scene_path"]
    baseline_sha = _sha256(baseline_path)
    candidate_sha = _sha256(candidate_path) if candidate_path.is_file() else None
    if baseline_sha != EXPECTED_BASELINE_SHA256:
        failures.append(f"protected baseline hash mismatch: {baseline_sha}")
    if lineage["parent_scene_sha256"] != baseline_sha:
        failures.append("catalog parent scene hash mismatch")
    if candidate_sha != lineage["candidate_initial_sha256"]:
        failures.append("candidate initial scene hash mismatch")
    if candidate_sha != baseline_sha:
        failures.append("Step1 candidate must be a byte-identical baseline copy")

    try:
        from pxr import Usd
    except ImportError:
        pass
    else:
        usd_parse_status = "pass"
        usd_paths = [PROJECT_ROOT / path for path in reference_paths]
        usd_paths.append(candidate_path)
        for usd_path in usd_paths:
            stage = Usd.Stage.Open(str(usd_path), Usd.Stage.LoadNone)
            if stage is None:
                failures.append(f"USD parser could not open {usd_path}")
                usd_parse_status = "fail"

    return {
        "status": "pass" if not failures else "fail",
        "catalog_path": CATALOG_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "asset_count": len(assets),
        "assets_per_class": dict(sorted(counts.items())),
        "assets_per_split": {
            split: len(asset_ids_for_split)
            for split, asset_ids_for_split in sorted(split_asset_ids.items())
        },
        "baseline_sha256": baseline_sha,
        "candidate_initial_sha256": candidate_sha,
        "usd_parse_status": usd_parse_status,
        "failures": failures,
    }


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "pass" else 1)
