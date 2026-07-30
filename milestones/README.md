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
6. the preceding milestone status and final handoff entry

## Required end-of-run update

Every execution must:

1. append one UTC-dated entry to the target milestone `LOG.md`;
2. update the target `STATUS.md` without deleting history from its log;
3. update `CURRENT.md` when state, blocker, evidence, commit, or next action
   changes;
4. cite durable evidence paths and the commit SHA when one exists;
5. disclose failed or blocked checks rather than changing them to pass.

Use one cumulative log per milestone. Raw retries and large evidence remain in
ignored `outputs/` or `validation/tmp/` locations.
