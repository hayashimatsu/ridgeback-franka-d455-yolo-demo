# D455 Baseline Import

Milestone M0 imports the minimum tracked foundation from
`hayashimatsu/ridgeback-franka-d455-demo` without modifying that source
repository.

## Source

- Local read-only reference: `/home/rci05/User/Lin/test_claude_mcp_04`
- Public repository: `https://github.com/hayashimatsu/ridgeback-franka-d455-demo`
- Source branch: `main`
- Source commit: `23aeb67d32cf4904a42f2c0cab714121e364529d`
- Machine-readable hashes: `validation/baseline/provenance.json`

The source had no tracked modifications during import. Its untracked
`docs/explanation-for-the-measurements.md` belongs to the user and was neither
read as import authority nor copied into this repository.

## Imported foundation

- The current source Ridgeback + Franka + D455 USD.
- GUI bootstrap, IK controller, and D455 capture scripts.
- The baseline demo manifest and operator documentation.
- The compact source release acceptance record and five reviewed golden images.

The imported acceptance record is historical release evidence. Its recorded
scene SHA-256 is `b3e83bd6...`, while the current imported scene SHA-256 is
`ce5690e4...`; therefore it does not prove the current imported scene, this
derived repository, or any future YOLO revision. A clean-reopen baseline check,
new scene, model, runtime pipeline, and final acceptance are still required by
`PROJECT_PROFILE.md`.

## Immutability rule

`scenes/ridgeback_franka_d455_demo.usd` is the imported baseline and must remain
unchanged. The first scene mutation must be saved as
`scenes/ridgeback_franka_d455_yolo_demo.usd` and validated independently.
