# Ridgeback + Franka + D455 YOLO Demo

An Isaac Sim project for real-time semantic perception from a wrist-mounted
stereo camera. The planned demo combines a Ridgeback + Franka Panda robot,
an Intel RealSense D455 camera model, YOLO instance segmentation, and depth
fusion to report visible object surfaces in world coordinates.

## Project status

**Milestone M0 complete: the current D455 source foundation has been imported
with exact provenance; YOLO and scene implementation have not started.**

The repository contains an unchanged copy of the current source USD, runtime
scripts, a historical compact acceptance record, and reviewed golden images. It
intentionally does not yet claim that the YOLO model, synthetic dataset,
factory shelf scene, or real-time perception pipeline exists. Planned artifacts
are marked as such in [PROJECT_PROFILE.md](PROJECT_PROFILE.md), and baseline
hashes are recorded in
[`validation/baseline/provenance.json`](validation/baseline/provenance.json).
The historical acceptance scene hash differs from the current imported scene
hash, so a clean-reopen baseline check is required before treating the imported
state as a new release candidate.

## Confirmed first release scope

- Recognize up to 20 visible objects from five fixed classes: box, bottle,
  hand tool, ball, and mechanical part.
- Use at least five visually distinct assets per class, with held-out asset
  identities for generalization testing.
- Run perception while the operator drags `/World/IKTarget` in the Isaac Sim
  GUI.
- Display class, confidence, measured visible-surface distance, visible-surface
  world coordinate, and visible 3D extent.
- Report uncertain depth-supported candidates as unknown instead of forcing a
  known class.
- Capture left/right RGB, depth evidence, YOLO visualization, surface
  measurements, and provenance without modifying the release USD.
- Keep autonomous grasping, motion planning, physical stereo disparity, and
  real-camera transfer outside the first release gate.

## Planned workflow

1. Derive a new scene revision from the validated
   `ridgeback-franka-d455-demo` project without modifying that source project.
2. Build a factory shelf asset catalog with six or more assets per class.
3. Generate labeled RGB and instance-mask data with Isaac Sim Replicator.
4. Fine-tune and validate a compact YOLO segmentation model in an isolated
   training environment.
5. Export and benchmark the fastest model that passes the documented accuracy
   gates.
6. Fuse YOLO masks with depth-aligned left-camera depth and the runtime camera
   pose.
7. Validate the complete Play > start script > drag IK target > live perception
   > capture workflow after a clean GUI reopen.

## Repository contract

- [PROJECT_PROFILE.md](PROJECT_PROFILE.md) is the authoritative user goal,
  planned file map, protection policy, and acceptance contract.
- [AGENTS.md](AGENTS.md) defines shared Isaac Sim safety, revision, routing,
  and verification rules.
- [CLAUDE.md](CLAUDE.md) defines Claude Code execution routes.
- [docs/BASELINE_IMPORT.md](docs/BASELINE_IMPORT.md) documents the immutable
  source foundation and its provenance.
- `.agents/skills/isaac-sim-mcp-workflow/` contains the reusable preflight and
  acceptance workflow.
- `validation/release_acceptance.template.json` is a template only; a release
  must produce and validate `validation/release_acceptance.json`.

## Source project protection

The confirmed source project is
`/home/rci05/User/Lin/test_claude_mcp_04`. It is an engineering reference and
must remain read-only. In particular, its accepted
`scenes/ridgeback_franka_d455_demo.usd` must not be overwritten. All scene work
for this repository will use a new revision.

## Routing

The selected implementation route is `OPUS_TO_SONNET`: architecture and
cross-system risk are reviewed first, followed by bounded implementation and
independent acceptance review.
