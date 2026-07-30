# Current Project Position

- Current gate: M0 clean-reopen baseline verification
- State: `blocked`
- Last completed milestone: M0 baseline import
- Last completed commit: `e2b4f44857ecf8a3b98df86917a17f7d2d312c1d`
- Expected immutable baseline SHA-256: `ce5690e406da8180555e425df7e07f298ddf25c0b2e87d4d70263fb5dd98dffa`
- Durable evidence: `validation/baseline/clean_reopen_check.json`
- Blocker: Isaac Sim and MCP are now available, but the active canonical USD
  has unsaved root-layer edits (`dirty=true`). Clean-reopen would discard that
  state and requires an explicit preserve-or-discard decision.
- Protected unexpected state: the canonical working-copy baseline USD is dirty
  with SHA-256 `c9631abf3c9bb9bce05b74b11bbd13514249d383c11251fd671c3cfd29d157a2`.
  It must not be overwritten, staged, or used as baseline evidence until its
  ownership and intent are resolved.
- Next action: decide whether the current dirty GUI state should be preserved as
  a separately named revision or discarded. Then reopen the clean committed M0
  baseline from a detached validation worktree and resume `M0/STATUS.md`.
- Next implementation owner after the gate passes: Agent 1, M1-M3.
