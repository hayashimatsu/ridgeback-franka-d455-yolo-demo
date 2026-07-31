# Milestone Continuity

This directory is the durable handoff surface for the seven implementation
milestones plus the M0 foundation. It answers four questions without relying on
conversation history:

1. Where is the project now?
2. What has already been proven or attempted?
3. What is the current blocker or next executable action?
4. Which agent owns the next dependent segment?

## Required reading order

Before milestone work, read:

1. `../PROJECT_PROFILE.md`
2. `CURRENT.md`
3. `AGENT_HANDOFF.md`
4. the target milestone `STATUS.md`
5. the target milestone `LOG.md`
6. the unique task file referenced by `CURRENT.md`
7. the preceding milestone status and final handoff entry

## Required end-of-run update

Every Claude execution must:

1. append one UTC-dated entry to the target milestone `LOG.md`;
2. cite evidence paths and disclose failed or blocked checks;
3. stop for Codex review without advancing the task or milestone.

Codex owns task files, `STATUS.md`, `CURRENT.md`, final acceptance, and the
default commit/push decision. After review, Codex appends a review entry and
either accepts the step or discusses and authors a follow-up task with the user.

Use one cumulative log per milestone. Raw retries and large evidence remain in
ignored `outputs/` or `validation/tmp/` locations.
