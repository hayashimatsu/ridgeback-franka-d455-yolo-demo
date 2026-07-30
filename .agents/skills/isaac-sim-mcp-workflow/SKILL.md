---
name: isaac-sim-mcp-workflow
description: Execute, diagnose, change, or validate NVIDIA Isaac Sim projects through the isaac-sim MCP server with bounded clarification, runtime-state correctness, minimal MCP calls, controlled USD saves, compact JSON evidence, and clean-reopen acceptance. Use for Isaac Sim scene, articulation, IK, camera, sensor, physics, capture, metrology, USD revision, or MCP troubleshooting tasks.
---

# Isaac Sim MCP Workflow

## Start from the project contract

1. Read `AGENTS.md`, `CLAUDE.md` when applicable, and `PROJECT_PROFILE.md`.
2. Read only the project documents named in `PROJECT_PROFILE.md`.
3. If a required profile field still contains `REPLACE_ME`, ask the user before mutating Isaac Sim or a USD.
4. Distinguish answer, diagnosis, change, validation, and release requests. Do not turn an explanation request into a scene mutation.

## Make the request executable

Resolve four fields before acting: objective, scope, acceptance, and authority. Ask a concise question only when an unknown could materially change the result, risk, acceptance test, or irreversible action. Group at most three blocking questions in one round. State reasonable non-blocking assumptions and proceed.

Read [routing.md](references/routing.md) when choosing Sonnet, Opus, Opus-to-Sonnet delegation, or an agent team.

## Preflight before live work

Run `scripts/preflight.sh` from the repository root. Confirm the active stage and timeline again inside Isaac Sim; CLI health alone does not prove the intended stage is open.

Before a mutation, record:

- active root-layer path and hash;
- timeline state;
- target prim paths;
- whether the requested operation is runtime-only or authored;
- whether saving a new USD revision is authorized.

Read [mcp-execution.md](references/mcp-execution.md) before sending MCP scripts or diagnosing a stale pose, black frame, callback, or render-product problem.

## Execute efficiently

1. Use reliable read-only MCP calls for connection and lightweight discovery.
2. Prefer checked-in reusable runtime functions over large one-off `execute_script` payloads.
3. Batch logically related observations that share one stage state, but keep mutations and acceptance independently inspectable.
4. Fail fast in this order: provenance and authored geometry, timeline and callbacks, runtime transforms, control motion, render setup, image/depth readback, full metrology.
5. While Play is active, read moving robot and camera poses from runtime articulation or Xform state, not authored USD transforms.
6. Never save live session state into the current release USD unless the user explicitly authorized that exact save. Create and validate a new revision for scene changes.
7. Keep probes and failed attempts in ignored scratch locations. Do not create a permanent JSON file for every tool call.

## Validate the claimed outcome

Read [acceptance.md](references/acceptance.md) and select only gates relevant to the claim. A release claim requires a clean reopen and the project-specific gates in `PROJECT_PROFILE.md`.

For camera claims, inspect representative images and raw depth; JSON statistics alone are insufficient. For rigid attachment, use two materially different reachable poses. For capture integrity, compare the root USD hash before and after.

Read [evidence-policy.md](references/evidence-policy.md) before writing evidence. Validate a release record with:

```bash
python3 .agents/skills/isaac-sim-mcp-workflow/scripts/validate_acceptance.py \
  validation/release_acceptance.json
```

## Stop and report honestly

Stop when permission, missing user authority, wrong active stage, unresolved provenance, or an unsafe save blocks the task. A failed probe is not a release failure unless it is part of the final gate. Report the exact blocker, retained artifacts, and smallest next action. Never convert incomplete evidence into `pass`.
