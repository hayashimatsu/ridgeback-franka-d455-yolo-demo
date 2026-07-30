# Understanding and Managing the Project-03 JSON Evidence

## What the files manage

The phase JSON files are machine-readable observations produced while agents
were building and debugging the Isaac Sim scene. They generally belong to five
categories:

| Category | Typical names | What it records |
|---|---|---|
| Discovery | `*_probe.json`, `*_discover.json` | Available APIs, prim paths, DOF names, assets, and transforms |
| Construction | `*_build.json`, `*_fix.json`, `*_save.json` | Which USD attributes or prims an agent attempted to change |
| Runtime state | `*_play.json`, `*_reopen.json`, `*_final_state.json` | Active stage, timeline, callback state, and values observed in one session |
| Diagnosis | `*_diag.json`, `*_rootcause.json`, numbered retries | Failed hypotheses, intermediate measurements, and solver experiments |
| Acceptance | `*_verify.json`, metrology measurements | Before/after values and pass/fail thresholds for a claimed milestone |

The original reason for file-based results was sound. The historical MCP
`execute_script` wrapper could report a serialization error even when its Python
code had completed inside Isaac Sim. Writing the real result to disk gave the
agent a reliable return channel and preserved exact numeric evidence.

## How to read one JSON file

Read it in this order:

1. Identify the file's purpose from its name and the matching phase report.
2. Find the stage path, root-layer identifier, file hash, and timestamp. Without
   provenance, the result may describe a different USD or a stale session.
3. Check `status`, `error`, `traceback`, or a final verdict field.
4. Check whether the timeline was playing and whether the result is pre-Play or
   post-Play.
5. Compare explicit before/after values rather than trusting a `success` string.
6. Find the acceptance threshold and confirm that every required item passed.
7. For camera claims, inspect the corresponding PNG and raw depth. JSON alone
   cannot prove that an image is visually useful.

For example, an attachment result should contain at least two different arm
poses and show that the hand-to-camera relative transform stayed invariant. A
single `timeline.play()` success or a camera prim that exists is not attachment
proof.

## Was the project-03 approach reasonable?

Using JSON as a runtime bridge and numeric evidence format was reasonable.
Keeping nearly every exploratory result forever at repository root was not an
effective release-management strategy.

Project 03 accumulated 293 JSON files. Most are small, so storage is not the
main problem. The management cost comes from:

- unclear authority between early probes and final verification;
- repeated `v2`, `v3`, `final`, and `final2` attempts;
- duplicated files in the root and run folders;
- successful and failed experiments mixed with release evidence;
- filenames that do not always identify the exact USD hash or session;
- later documents continuing to cite superseded evidence.

The files are useful as an engineering archive, but they should not be copied
into a demo repository or presented as the normal operator interface.

## Why ten phases appeared from a few user commands

A user command can contain several independent engineering uncertainties:
asset discovery, physics attachment, IK control, camera initialization, render
readback, transforms, metrology, and persistence after reopen. Separating those
risks is normal. The avoidable problem was that agents often treated every probe
or correction as a new permanent phase and did not consolidate evidence after a
milestone passed.

The process also repeated work because requirements and test convenience were
not kept separate. The horizontal r9 metrology pose, for example, improved a
depth test but conflicted with the intended static wrist pose. Later work then
had to undo the pose mismatch. Similar repetition came from diagnosing a camera
image before checking its authored geometry and from allowing live session state
to be saved into USD files.

Phase count should therefore not be equated with user command count. A good
agent may run many bounded internal checks, but the user-facing workflow should
still consolidate them into a few meaningful milestones.

## Evidence policy for project 04

Project 04 uses three evidence levels:

1. **Scratch evidence** — temporary probes and failed experiments under
   `outputs/` or `validation/tmp/`; ignored by Git.
2. **Capture record** — one `capture.json` inside each unique runtime capture
   directory; also ignored because it is reproducible operator output.
3. **Release acceptance** — one compact reviewed acceptance record plus only
   the minimum representative golden images; committed with the matching scene
   and scripts.

`measurements.json` is the single complete operator report beside
`capture.json`, not another phase artifact. Its
`reported_targets_near_to_far` array contains only depth-supported reported
targets. Camera and world coordinates
describe the same representative sample. Bounds and depth percentiles describe
the visible range; `depth_region_labels.npy` plus raw axial depth preserves the
exact samples for non-planar surfaces. Known floor regions appear only under
`excluded_environment_regions` and in the raw label evidence. Optional USD prim names are marked
`used_for_depth_detection: false` and never cause an unseen stage object to
appear in the report.

`summary.json` is a compact projection of `measurements.json`, not another
measurement or additional phase evidence. It deliberately omits detector
diagnostics. Use it to compare near-to-far camera ranges and measured visible
surface world coordinates with the GUI. Remember that GUI Translate normally
describes a prim center/origin, while depth describes the first visible surface.

A release acceptance record should contain:

- schema version and acceptance result;
- exact active-stage path and SHA-256;
- Isaac Sim version and physics backend;
- timeline and callback state;
- numeric results for Play stability, attachment, stereo baseline, RGB energy,
  depth validity, and output uniqueness;
- links or relative paths to the selected golden images;
- failures and known limitations.

This keeps the reproducibility benefits of JSON without turning every internal
agent action into permanent repository structure.

## A more efficient three-milestone model

1. **Prepare** — agree on the visible GUI workflow and create one candidate
   scene plus its runtime entry points.
2. **Validate** — run all internal probes in scratch space, correct failures,
   and publish one consolidated acceptance result.
3. **Release** — update the scene, scripts, manifest, runbook, and acceptance in
   one reviewed Git commit.

Additional probes are allowed inside a milestone, but they do not become new
permanent phases unless they establish a reusable capability or a distinct
release boundary.
