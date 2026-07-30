# M0 Status — Foundation and Baseline Verification

- Owner: Codex / project bootstrap
- State: `blocked`
- Import result: `complete`
- Clean-reopen result: `blocked`
- Completed commit: `e2b4f44857ecf8a3b98df86917a17f7d2d312c1d`
- Imported-file verification: pass, 14 of 14 hashes
- Clean validation source: detached worktree at commit `e2b4f44`
- Blocker: Isaac Sim GUI and MCP are connected, but the active canonical
  baseline root layer is dirty. Reopening another stage would discard unsaved
  authored state without a preserve-or-discard decision.
- Unexpected protected state: canonical baseline USD is dirty and remains
  untouched.

## Remaining gates

- Open the clean committed baseline USD in a fresh Isaac Sim GUI session.
- Confirm active root-layer path and SHA-256.
- Confirm Play stability and one IK callback.
- Exercise two materially different reachable IK poses.
- Confirm D455 hand-relative rigidity across both poses.
- Produce two non-overwriting captures with non-black RGB, valid depth, stereo
  baseline within tolerance, restored target visibility, and unchanged USD hash.
- Stop controller and timeline; record final state.

M1 must not start until these gates pass or the user explicitly changes the
project contract.
