#!/usr/bin/env python3
import json
import pathlib
import re
import sys


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


if len(sys.argv) != 2:
    fail("usage: validate_acceptance.py <release_acceptance.json>")

path = pathlib.Path(sys.argv[1])
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except FileNotFoundError:
    fail(f"missing file: {path}")
except json.JSONDecodeError as exc:
    fail(f"invalid JSON: {exc}")

required = ["schema_version", "run_id", "timestamp_utc", "result", "stage", "checks", "failures", "known_limitations"]
missing = [key for key in required if key not in data]
if missing:
    fail("missing keys: " + ", ".join(missing))

if data["result"] not in {"pass", "fail", "blocked"}:
    fail("result must be pass, fail, or blocked")

stage = data["stage"]
if not isinstance(stage, dict) or not stage.get("path"):
    fail("stage.path is required")
sha = stage.get("sha256", "")
if not re.fullmatch(r"[0-9a-f]{64}", sha):
    fail("stage.sha256 must be 64 lowercase hexadecimal characters")

checks = data["checks"]
if not isinstance(checks, list) or not checks:
    fail("checks must be a non-empty list")
for index, check in enumerate(checks):
    if not isinstance(check, dict):
        fail(f"checks[{index}] must be an object")
    for key in ("name", "result", "observed", "criterion"):
        if key not in check:
            fail(f"checks[{index}] is missing {key}")
    if check["result"] not in {"pass", "fail", "not_run"}:
        fail(f"checks[{index}].result is invalid")

if data["result"] == "pass":
    nonpassing = [check["name"] for check in checks if check["result"] != "pass"]
    if nonpassing:
        fail("overall pass conflicts with checks: " + ", ".join(nonpassing))
    if data["failures"]:
        fail("overall pass cannot contain failures")

print(f"PASS: {path} has a consistent compact acceptance schema")
