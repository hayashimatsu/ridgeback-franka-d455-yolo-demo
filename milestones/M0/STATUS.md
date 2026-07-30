# M0 Status — Foundation and Baseline Verification

- Owner: Codex / project bootstrap
- State: `in_progress`
- Import result: `complete`
- Clean-reopen result: `blocked`
- Completed commit: `e2b4f44857ecf8a3b98df86917a17f7d2d312c1d`
- Imported-file verification: pass, 14 of 14 hashes
- Clean validation source: detached worktree at commit `e2b4f44`
- Reviewed baseline save: complete with explicit user authority; SHA-256
  `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
- Blocker: none; clean-reopen runtime gates remain pending.
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
