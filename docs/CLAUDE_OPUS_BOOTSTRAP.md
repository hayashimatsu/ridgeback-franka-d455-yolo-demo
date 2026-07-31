# Claude Code Opus Execution-Lead Bootstrap

This is the permanent startup contract for every new Claude Code Opus
conversation in this repository. It is milestone-independent. The current work
is always the single ready task referenced by `milestones/CURRENT.md`.

## Startup reading order

From the repository root, fully read:

1. `AGENTS.md`
2. `CLAUDE.md`
3. `README.md`
4. `PROJECT_PROFILE.md`
5. `milestones/CURRENT.md`
6. `milestones/AGENT_HANDOFF.md`
7. the current milestone `STATUS.md`
8. the current milestone cumulative `LOG.md`
9. the exact task file referenced by `CURRENT.md`
10. `.agents/skills/isaac-sim-mcp-workflow/SKILL.md`
11. every additional file required by the task or skill

Stop without execution when `CURRENT.md` does not identify exactly one ready
task, the task file is missing, required facts conflict, or the observed Git or
USD state violates the task preconditions. Do not infer work from an old Claude
session, chat history, or the next milestone description.

## Execution ownership

Claude Code Opus is the current task's execution lead. Opus may execute directly
or delegate bounded subtasks to Sonnet. Opus must define objective, scope,
allowed files/prims, acceptance, authority, and stop conditions for every
delegation; avoid concurrent writers; inspect delegated diffs and evidence; and
record the delegation. Opus retains responsibility for the integrated result.

Codex is the project architect and final acceptance owner. Unless the task
explicitly grants broader authority, Claude must not mark `STATUS.md` complete,
advance `CURRENT.md`, commit, push, or begin another task.

## Isaac Sim preflight

Before live work, verify all applicable facts:

1. Git branch, HEAD, and working-tree state.
2. Protected and candidate USD paths and disk SHA-256 values.
3. `claude mcp list` reports `isaac-sim` connected in the normal terminal.
4. Isaac MCP `get_scene_info` succeeds.
5. Active root-layer path, timeline state, and root dirty state inside Isaac Sim.
6. Required prims and the task's runtime-only versus authored-change authority.

MCP registration health never proves that the intended stage is active. Never
save a protected scene, or persist runtime pose, session visibility, render
products, callbacks, or diagnostics into a release candidate without explicit
task authority.

## Known execute-script behavior

The Isaac MCP `execute_script` wrapper can report a Pydantic `string_type` error
after a Python payload successfully executed and returned `None` or a mapping.
Do not classify the wrapper message alone as failure.

For a result-bearing payload, write one fresh ignored JSON envelope before the
payload returns. Include timestamp, status, active-stage path, hashes, timeline,
result, error, and traceback. If the known wrapper error occurs, read that
envelope and verify it belongs to the current attempt. Missing, stale,
incomplete, or failed evidence is a failure; a fresh complete envelope is the
operation authority. Keep retries under `validation/tmp/` or `outputs/`.

## Verification and logging

Apply the task acceptance gates and report `pass`, `fail`, `blocked`, or
`not_run` honestly. Camera claims require direct inspection of representative
images and raw depth. Runtime-only work requires before/after disk hashes.

At the end of every execution, append one UTC-dated entry to the current
milestone `LOG.md`. Summarize logical engineering operations rather than every
Read or MCP call. Include:

- task ID and task path;
- objective and initial Git/runtime/USD state;
- Opus strategy and every Sonnet delegation;
- files and prims touched;
- runtime observations and task-level checks;
- evidence paths, failed probes, retries, and limitations;
- stop-condition outcome and ending Git status/diff;
- remaining work and the exact points Codex must review;
- the statement `Waiting for Codex review; did not start another task.`

Then report the task result and stop. Do not self-approve the milestone.

## Standard new-conversation instruction

The user may start a new Opus conversation with:

```text
Read `docs/CLAUDE_OPUS_BOOTSTRAP.md` completely, follow its reading order, then
execute only the ready task referenced by `milestones/CURRENT.md`. Decide as
Opus whether bounded Sonnet delegation is useful. Append the current milestone
LOG and stop for Codex review without committing, pushing, advancing the task,
or starting another milestone unless the task explicitly grants that authority.
```
