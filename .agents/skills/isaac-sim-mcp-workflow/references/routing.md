# Model and Delegation Routing

Choose the cheapest route that preserves correctness. File count and line count are weak proxies; use uncertainty, risk, coupling, and validation cost.

## Routes

### SONNET

Use one Sonnet main session when all are true:

- objective and acceptance are already concrete;
- the task affects one subsystem or follows a documented operation;
- no architectural choice or competing diagnosis is required;
- failures are reversible and do not require saving over a release USD;
- one executor can implement and verify without losing critical context.

Examples: run a known capture, inspect a prim, apply a bounded script fix, repeat a documented acceptance check.

### OPUS

Use one Opus session for reasoning or review without a separate executor when the deliverable is primarily diagnosis, architecture, requirement reconciliation, or an evidence audit.

### OPUS_TO_SONNET

Use Opus as the main orchestrator and delegate bounded implementation to the `isaac-sim-executor` Sonnet agent when any applies:

- requirements conflict or acceptance must be designed;
- scene authoring crosses physics, articulation, camera, render, or persistence boundaries;
- the task changes a release candidate or needs a new USD revision;
- prior attempts failed for different reasons;
- provenance, runtime/authored state, or save authority is material;
- an independent final evidence review is valuable.

Opus must send the executor an exact objective, allowed files/prims, forbidden changes, required checks, output location, and stop conditions. Resume the same executor for related follow-up work instead of repeatedly spawning fresh contexts.

### AGENT_TEAM

Recommend an agent team only when at least two workstreams are genuinely independent, use distinct files or read-only hypotheses, and parallel time saved is expected to exceed coordination cost. Appropriate cases include competing root-cause hypotheses, independent security/performance reviews, or separate code and acceptance-harness modules.

Do not use a team for sequential work, same-USD edits, one small fix, or tasks where every worker needs the previous worker's result. Agent teams are experimental; obtain user confirmation before enabling them.

## Codex routing output

When handing work to Claude Code, report:

```text
ROUTE: SONNET | OPUS | OPUS_TO_SONNET | AGENT_TEAM
WHY: one sentence tied to uncertainty, risk, coupling, and validation cost
OBJECTIVE: testable outcome
SCOPE: allowed files, prims, and runtime actions
ACCEPTANCE: observable pass conditions
AUTHORITY: allowed saves, commits, and external actions
STOP: conditions that require returning to the user
```

Do not add this ceremony when Codex can answer a simple question directly without a Claude handoff.
