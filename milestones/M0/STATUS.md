# M0 Status — Foundation and Baseline Verification

- Owner: Codex / project bootstrap
- State: `complete`
- Import result: `complete`
- Clean-reopen result: `pass`
- Reviewed baseline commit: `6d3e435ac220a4fe5b5e20bf0ceacd8369fb7c9b`
- Imported-file verification: pass, 14 of 14 hashes
- Clean validation source: detached worktree at commit `e2b4f44`
- Reviewed baseline save: complete with explicit user authority; SHA-256
  `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
- Runtime verification: pass for Play stability, IK lifecycle and two poses,
  D455 rigidity, two unique captures, RGB/depth, stereo baseline, visible
  surface measurement, cleanup, and root USD immutability.
- Known limitation: Isaac Sim marks the root layer dirty immediately after
  reopen due to runtime/render authored state, but the on-disk SHA-256 remained
  unchanged throughout acceptance.

## Completed gates

- Open the clean committed baseline USD in a fresh Isaac Sim GUI session.
- Confirm active root-layer path and SHA-256.
- Confirm Play stability and one IK callback.
- Exercise two materially different reachable IK poses.
- Confirm D455 hand-relative rigidity across both poses.
- Produce two non-overwriting captures with non-black RGB, valid depth, stereo
  baseline within tolerance, restored target visibility, and unchanged USD hash.
- Stop controller and timeline; record final state.

M1 may now start from reviewed baseline commit `6d3e435`; it must create a new
scene revision and must not edit the imported baseline USD.
