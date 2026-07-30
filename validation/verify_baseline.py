#!/usr/bin/env python3
"""Verify that imported M0 baseline files still match recorded source hashes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROVENANCE_PATH = REPOSITORY_ROOT / "validation" / "baseline" / "provenance.json"
REVIEWED_BASELINE_PATH = (
    REPOSITORY_ROOT / "validation" / "baseline" / "reviewed_baseline.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    reviewed_baseline = (
        json.loads(REVIEWED_BASELINE_PATH.read_text(encoding="utf-8"))
        if REVIEWED_BASELINE_PATH.is_file()
        else None
    )
    failures: list[dict[str, str]] = []

    for record in provenance["files"]:
        relative_path = Path(record["path"])
        candidate = (REPOSITORY_ROOT / relative_path).resolve()
        try:
            candidate.relative_to(REPOSITORY_ROOT.resolve())
        except ValueError:
            failures.append(
                {
                    "path": record["path"],
                    "reason": "path escapes repository root",
                }
            )
            continue

        if not candidate.is_file():
            failures.append({"path": record["path"], "reason": "missing"})
            continue

        expected = record["sha256"]
        if (
            reviewed_baseline is not None
            and record["path"] == reviewed_baseline["reviewed_scene"]["path"]
        ):
            expected = reviewed_baseline["reviewed_scene"]["sha256"]

        observed = sha256(candidate)
        if observed != expected:
            failures.append(
                {
                    "path": record["path"],
                    "reason": "sha256 mismatch",
                    "expected": expected,
                    "observed": observed,
                }
            )

    compatibility = provenance["acceptance_compatibility"]
    imported_scene = REPOSITORY_ROOT / "scenes" / "ridgeback_franka_d455_demo.usd"
    observed_scene_hash = sha256(imported_scene) if imported_scene.is_file() else None
    current_expected_scene_hash = (
        reviewed_baseline["reviewed_scene"]["sha256"]
        if reviewed_baseline is not None
        else compatibility["imported_scene_sha256"]
    )
    if observed_scene_hash != current_expected_scene_hash:
        failures.append(
            {
                "path": "scenes/ridgeback_franka_d455_demo.usd",
                "reason": "scene does not match acceptance-compatibility record",
                "expected": current_expected_scene_hash,
                "observed": str(observed_scene_hash),
            }
        )

    result = {
        "status": "pass" if not failures else "fail",
        "verified_file_count": len(provenance["files"]),
        "source_commit": provenance["source"]["commit"],
        "reviewed_baseline_present": reviewed_baseline is not None,
        "current_scene_sha256": observed_scene_hash,
        "historical_acceptance_matches_imported_scene": compatibility[
            "matches_imported_scene"
        ],
        "failures": failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
