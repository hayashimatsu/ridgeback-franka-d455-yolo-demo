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

Use one Opus execution-lead session when Codex has already written a complete
current task contract. Opus may implement directly or delegate bounded work to
Sonnet, but it owns integration, task-level verification, and the milestone log.
Codex remains the final acceptance and commit owner.

### OPUS_TO_SONNET

This is a legacy explicit-delegation route. Use it only when the current task
requires Opus to create a specific Sonnet execution stream. The default project
route is `OPUS`, in which Opus decides whether delegation is useful.

Explicit delegation may still be appropriate when any applies:

- requirements conflict or acceptance must be designed;
- scene authoring crosses physics, articulation, camera, render, or persistence boundaries;
- the task changes a release candidate or needs a new USD revision;
- prior attempts failed for different reasons;
- provenance, runtime/authored state, or save authority is material;
- an independent final evidence review is valuable.

Opus must send the executor an exact objective, allowed files/prims, forbidden
changes, required checks, output location, and stop conditions. Opus must review
the result and prevent concurrent writers for shared artifacts.

### AGENT_TEAM

Recommend an agent team only when at least two workstreams are genuinely independent, use distinct files or read-only hypotheses, and parallel time saved is expected to exceed coordination cost. Appropriate cases include competing root-cause hypotheses, independent security/performance reviews, or separate code and acceptance-harness modules.

Do not use a team for sequential work, same-USD edits, one small fix, or tasks where every worker needs the previous worker's result. Agent teams are experimental; obtain user confirmation before enabling them.

## Codex routing output

When Codex authors a Claude task, record:

```text
ROUTE: SONNET | OPUS | OPUS_TO_SONNET | AGENT_TEAM
WHY: one sentence tied to uncertainty, risk, coupling, and validation cost
OBJECTIVE: testable outcome
SCOPE: allowed files, prims, and runtime actions
ACCEPTANCE: observable pass conditions
AUTHORITY: allowed saves, commits, and external actions
STOP: conditions that require returning to the user
```

The durable version belongs in the task file referenced by
`milestones/CURRENT.md`; conversation text is not the task authority.
