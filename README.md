# Ridgeback + Franka + D455 YOLO Demo

An Isaac Sim project for real-time semantic perception from a wrist-mounted
stereo camera. The planned demo combines a Ridgeback + Franka Panda robot,
an Intel RealSense D455 camera model, YOLO instance segmentation, and depth
fusion to report visible object surfaces in world coordinates.

## Project status

**Milestone M0 complete: the reviewed D455 source foundation has passed its
clean-reopen runtime acceptance; YOLO and factory-scene implementation have not
started.**

The repository contains a user-reviewed derivative of the source USD, imported
runtime scripts, a historical compact acceptance record, and reviewed golden images. It
intentionally does not yet claim that the YOLO model, synthetic dataset,
factory shelf scene, or real-time perception pipeline exists. Planned artifacts
are marked as such in [PROJECT_PROFILE.md](PROJECT_PROFILE.md), and baseline
hashes are recorded in
[`validation/baseline/provenance.json`](validation/baseline/provenance.json).
The reviewed baseline is commit `6d3e435` with scene SHA-256 `a724cd7d...`.
Its clean-reopen evidence is recorded in
`validation/baseline/clean_reopen_check.json`; M1 must derive a new scene rather
than modify this baseline.

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
- [milestones/CURRENT.md](milestones/CURRENT.md) identifies the current project
  position, blocker, evidence, and next action.
- [milestones/AGENT_HANDOFF.md](milestones/AGENT_HANDOFF.md) defines the
  sequential M1-M3, M4-M5, and M6-M7 agent ownership contract.
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

The selected implementation route is `OPUS`: Codex and the user define one
durable milestone task, Claude Code Opus executes it and may delegate bounded
subtasks to Sonnet, and Codex independently reviews runtime evidence and decides
acceptance, follow-up, commit, and push.
