# Isaac Sim Agent Project Rules

## Purpose

Use critical reasoning to satisfy the user's actual goal with the fewest reliable operations. Optimize for correctness, reversibility, observable acceptance, and low coordination cost rather than the appearance of activity.

## Start gate

Before live Isaac Sim work or runtime-script changes:

1. Read `README.md`, `PROJECT_PROFILE.md`, and the project documents listed there.
2. Resolve objective, scope, acceptance, and authority.
3. Ask the user when a material unknown would change the output, risk, acceptance, save target, or irreversible action. Group at most three blocking questions per round.
4. State non-blocking assumptions and proceed once the task is executable.
5. Use the `isaac-sim-mcp-workflow` skill for scene, physics, articulation, IK, camera, sensor, capture, metrology, USD, or Isaac MCP tasks.

## Codex routing responsibility

Codex decides the Claude route from complexity, uncertainty, risk, subsystem coupling, and validation cost:

- `SONNET`: concrete, bounded, reversible work in one subsystem.
- `OPUS`: diagnosis, architecture, requirement reconciliation, or evidence review without a separate implementation stream.
- `OPUS_TO_SONNET`: high-risk or cross-system work where Opus defines and reviews a bounded Sonnet execution task.
- `AGENT_TEAM`: only genuinely independent parallel workstreams whose expected time savings exceed coordination cost; ask the user before enabling this experimental, higher-cost route.

Do not route by line count alone. Do not use multiple agents for sequential work or same-USD edits.

## Change and safety policy

- Preserve existing user changes and unrelated dirty files.
- Treat the current release USD as immutable unless the user explicitly authorizes replacing it.
- Create a new scene revision for scene changes; validate it before changing any default pointer.
- Do not save live session or diagnostic state into a release USD accidentally.
- While Play is active, read moving robot and camera world poses from runtime articulation/Xform state.
- Use scripts for repeatable, numeric, or multi-step operations; prefer safe GUI operations when they are clearer for the user.
- Keep probes and retries under ignored `outputs/` or `validation/tmp/` paths.
- Never create one permanent phase JSON per MCP call. Keep one compact release acceptance record.

## Verification and reporting

- Diagnose when asked to diagnose; do not silently implement a fix.
- For changes, run the smallest relevant check first, then the documented acceptance gate.
- A release claim requires a clean GUI reopen and the gates in `PROJECT_PROFILE.md`.
- Inspect representative images for camera claims; JSON alone does not prove visual usefulness.
- Inspect the staged diff before any commit. Commit only when the user requested or clearly authorized it.
- Report outcome, evidence, limitations, and the next user action. Never hide failed probes or call incomplete work a pass.
