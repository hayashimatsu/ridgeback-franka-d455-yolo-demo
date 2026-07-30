# M0 Cumulative Log

## 2026-07-30T08:23:33Z — Baseline import

- Imported the current tracked D455 USD, runtime scripts, documentation,
  historical acceptance record, and five golden images from source commit
  `23aeb67d32cf4904a42f2c0cab714121e364529d`.
- Preserved the source repository and its untracked
  `docs/explanation-for-the-measurements.md` unchanged.
- Added `validation/baseline/provenance.json` and a reusable 14-file hash check.
- Found that the historical acceptance scene hash `b3e83bd6...` differs from
  the imported scene hash `ce5690e4...`; did not inherit the old pass claim.
- Committed and pushed M0 as `e2b4f44857ecf8a3b98df86917a17f7d2d312c1d`.

## 2026-07-30T23:51:09Z — Clean-reopen attempt blocked

- Found the canonical working-copy baseline USD unexpectedly modified:
  `ce5690e4...` expected, `c9631abf...` observed. Preserved it without staging,
  restoring, or opening it as baseline evidence.
- Created a detached clean validation worktree at committed M0 SHA `e2b4f44`.
- Re-ran baseline provenance verification: pass, 14 of 14 files.
- Project preflight found the Claude `isaac-sim` MCP registration but could not
  connect.
- Codex `get_scene_info` also failed because no Isaac Sim extension was
  available.
- Process inspection found no running Isaac Sim or Kit process.
- Requested authorization to start Isaac Sim 6.0 with the existing MCP
  extension; authorization was not granted, so no GUI or live checks ran.
- Recorded the logical operation in
  `validation/baseline/clean_reopen_check.json` as `blocked`, not `fail`.
- Next action: start a fresh Isaac Sim GUI with MCP enabled and resume the
  remaining gates from the clean committed worktree.

## 2026-07-30T23:53:08Z — Runtime restored; dirty active stage protected

- The user started Isaac Sim and the Codex MCP ping succeeded against Isaac Sim
  Assets 6.0.
- Because the MCP response wrapper cannot serialize `None`, wrote one ignored
  active-stage probe to `validation/tmp/active_stage_probe.json`.
- Observed the active stage as the canonical working-copy
  `scenes/ridgeback_franka_d455_demo.usd`, with timeline stopped and root layer
  `dirty=true`.
- Did not switch stages, save, reload, or discard the dirty authored state.
- Clean-reopen remains blocked pending an explicit decision to preserve the
  current GUI state as a separate revision or discard it before opening the
  clean committed validation worktree.

## 2026-07-30T23:56:52Z — User-reviewed USD saved for commit

- The user explicitly authorized saving and committing the current active USD
  as the reviewed baseline.
- Confirmed the active root path matched the canonical project USD and the
  timeline was stopped before saving.
- Saved only the root layer: `dirty=true` before, `dirty=false` after.
- Disk SHA-256 changed from `c9631abf...` to `a724cd7d...` after the final save.
- Compared the committed M0 and reviewed layers as USDA: 2,268 versus 2,410
  lines and 517 unified-diff lines. Observed changes include viewport camera
  state, render settings, and Replicator render products.
- Added `validation/baseline/reviewed_baseline.json`; clean-reopen acceptance is
  still required before calling the reviewed scene a passing baseline.
