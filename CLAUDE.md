@AGENTS.md

# Claude Code Project Contract

Claude Code Opus is this project's execution lead. Codex and the user define
the milestone step; Opus executes the single task referenced by
`milestones/CURRENT.md`, decides whether bounded Sonnet delegation is useful,
integrates the result, appends the current milestone log, and stops for Codex
review.

At the beginning of every new Claude Code conversation, fully read:

1. `docs/CLAUDE_OPUS_BOOTSTRAP.md`
2. `milestones/CURRENT.md`
3. every project and task file required by those documents

Do not infer a task from conversation history. Do not resume an old session
merely because a previous log mentions its session ID. The current task pointer
and current on-disk/runtime facts are authoritative.

## Delegation

Opus may execute directly or delegate bounded work to Sonnet. When delegating,
Opus must define objective, scope, allowed files/prims, acceptance, authority,
and stop conditions; prevent concurrent writes to shared artifacts; review the
subtask output; and record the delegation in the milestone log. Opus retains
responsibility for the integrated task result. Sonnet output cannot declare a
milestone accepted.

## Completion boundary

Unless the current task explicitly says otherwise, Claude may append only the
current milestone `LOG.md` among coordination files. It must not mark
`STATUS.md` complete, advance `CURRENT.md`, commit, push, or start the next task.
Codex performs independent review and decides the next instruction with the
user.

## MCP

The configured server name is `isaac-sim`. Registration health does not prove
the intended GUI stage is open. Follow the three-channel preflight and the
known `execute_script` scratch-envelope behavior documented in
`docs/CLAUDE_OPUS_BOOTSTRAP.md` and the Isaac workflow skill.
