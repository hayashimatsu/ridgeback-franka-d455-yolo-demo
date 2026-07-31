# M1 Cumulative Log

No execution has started. Entry gate M0 is blocked.

## 2026-07-31T00:32:38Z — M1-Step1 asset catalog and scene foundation

- Objective: complete the first of at most three M1 execution batches by
  reconciling the M0 entry gate, establishing licensed/source-traceable object
  identities, and creating a protected-baseline-derived candidate scene without
  starting factory-scene layout.
- Template check: no dedicated milestone LOG, STATUS, or CURRENT template exists.
  This entry follows `milestones/README.md`, `AGENTS.md`, the cumulative M0 log
  pattern, and the user-supplied required fields. The earlier line stating that
  M0 is blocked is retained as history and corrected here by direct M0 evidence.
- Execution:
  - Re-read the project workflow and its routing, MCP execution, acceptance, and
    evidence references.
  - Confirmed `main`, local `origin/main`, and HEAD all pointed to
    `439015e93fa47ffea75de0329d41c3dba61ab220`; the working tree was clean before
    this run.
  - Confirmed M0 is complete from `milestones/M0/STATUS.md` and
    `validation/baseline/clean_reopen_check.json`; M1 entry gate is open.
  - Ran the workflow preflight. Claude CLI resolved the user-level `isaac-sim`
    registration but could not connect; the separate Codex Isaac MCP ping passed
    against Isaac Sim Assets 6.0.
  - Recorded the live active-stage identity, root dirty state, timeline state,
    and disk hash in one `/tmp` scratch probe before authoring files.
  - Copied the protected baseline from disk to
    `scenes/ridgeback_franka_d455_yolo_demo.usd`; did not save, reload, or switch
    the dirty live baseline stage.
  - Added a reproducible generator for 30 project-authored procedural proxy
    assets and generated six assets for each fixed class. Each class uses three
    train, two validation, and one held-out identity.
  - Created `config/object_catalog.yaml` in JSON-compatible YAML 1.2 syntax with
    fixed class IDs/names, stable asset IDs, semantic labels, USD/default prim
    paths, source, license/use conditions, redistribution policy, asset hashes,
    nominal dimensions, scale ranges, split identity, availability, and known
    limitations.
  - Added and ran `validation/validate_m1_step1.py`. Dependency-free catalog,
    identity, split, file-hash, and scene-lineage checks passed. Because offline
    Python did not expose `pxr`, a read-only Isaac Kit probe used
    `Sdf.Layer.FindOrOpen` and parsed all 31 layers successfully.
- Modified files:
  - `scenes/ridgeback_franka_d455_yolo_demo.usd`
  - `config/object_catalog.yaml`
  - `scripts/build_m1_object_assets.py`
  - `validation/validate_m1_step1.py`
  - 30 generated files under `assets/objects/{box,bottle,hand_tool,ball,mechanical_part}/`
  - `milestones/M1/LOG.md`, `milestones/M1/STATUS.md`, and
    `milestones/CURRENT.md`
- Isaac Sim active stage: remained
  `/home/rci05/User/Lin/test_codex_claude_mcp_1/ridgeback-franka-d455-yolo-demo/scenes/ridgeback_franka_d455_demo.usd`;
  timeline stopped; root layer reported `dirty=true`; no live stage save or
  authored prim mutation was performed.
- USD hashes:
  - Protected baseline before and after:
    `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
  - Candidate initial scene:
    `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`,
    byte-identical to the protected parent before Step2 authoring.
  - Object catalog:
    `54c6b4a72269642b74ad8c71146205d287bcaf6e70932041757e8a9744efa00e`.
- Acceptance result: M1-Step1 `pass`; overall M1 remains `in_progress`. Five
  taxonomy entries, 30 unique assets, six assets per class, split totals of 15
  train / 10 validation / 5 held-out, zero identity overlap, all asset hashes,
  and all 31 USD layers passed. Factory layout, semantic API authoring, visual
  review, Play/IK/D455 checks, and clean-reopen acceptance were not run and are
  not claimed.
- Failed probes:
  - Claude CLI preflight could not connect to its registered `isaac-sim` MCP.
    Codex MCP remained available, so no server configuration was changed.
  - The MCP `execute_script` response wrapper rejected a successful `None`
    result; the single `/tmp` result envelopes confirmed both probes completed.
  - System Python and offline Isaac `python.sh` did not expose `pxr`; USD parsing
    was therefore repeated inside the connected Isaac Kit process and passed.
- Known limitations:
  - The repository has no `LICENSE` file. All generated assets use license
    identifier `NOASSERTION`, are authorized for this project work, and are
    marked `redistribution_allowed=false` until the repository owner supplies
    standalone terms.
  - Assets are deliberately simple project-authored proxies, not external
    SimReady assets. Their scene composition, materials, and semantic API labels
    remain Step2 work.
  - The live protected baseline root is dirty due to the already documented
    reopen/render state and must never be saved over the protected USD.
- Commit SHA: not yet committed. The run started from
  `439015e93fa47ffea75de0329d41c3dba61ab220`; the M1 milestone commit remains
  deferred until the staged diff and full M1 acceptance are complete.
- Next smallest action: M1-Step2 authors only the candidate scene, references the
  catalog assets into a factory shelf layout visible to the D455, applies real
  semantic labels, and runs the smallest Play/IK/D455/visual checks without
  changing the protected baseline.

## 2026-07-31T00:49:40Z — Claude MCP connectivity diagnosis correction

- Objective: reconcile the user's successful terminal `claude mcp list` result
  with the failed Claude MCP health probes reported during M1-Step1.
- Execution:
  - Confirmed the Codex sandbox uses Claude Code 2.1.220 at
    `/home/rci05/.nvm/versions/node/v22.23.1/bin/claude`.
  - Re-ran `claude mcp list`, `claude mcp get isaac-sim`, and the project
    preflight inside the Codex sandbox; all three reproduced `Connection closed`.
  - With explicit approval, re-ran the same read-only `claude mcp list` outside
    the sandbox; `isaac-sim` reported `Connected`.
  - With explicit approval, independently re-ran
    `claude mcp get isaac-sim` outside the sandbox; the user-scope stdio
    registration and connection both reported healthy.
- Modified files: only `milestones/M1/LOG.md` for this correction entry; no USD,
  catalog, asset, script, MCP registration, credential, or user configuration
  was changed.
- Isaac Sim active stage: not queried or changed by this diagnosis. The most
  recent M1-Step1 postflight remains the protected baseline stage with timeline
  stopped and no disk mutation.
- USD hash: not recomputed because no scene/runtime operation occurred; the most
  recent protected baseline evidence remains
  `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
- Acceptance result: connectivity diagnosis `pass`. The Claude MCP registration
  and server are connected in the normal terminal/unsandboxed environment. The
  earlier failure is a Codex sandbox health-check false negative, not a broken
  registration or stopped Isaac Sim MCP server.
- Failed probes: all sandboxed Claude health commands still return MCP error
  `-32000` / `Connection closed`; retained as evidence of the environment
  boundary rather than server failure.
- Known limitation: the repository preflight script will continue to fail when
  invoked inside this restricted Codex sandbox. Future live-work preflight must
  run the Claude health check with approved unsandboxed execution, while active
  stage and timeline still require a separate in-Isaac verification.
- Commit SHA: not yet committed; M1 work remains based on
  `439015e93fa47ffea75de0329d41c3dba61ab220` pending the M1-Step3 acceptance
  commit.
- Next smallest action: proceed with M1-Step2 using an approved unsandboxed
  Claude MCP health check plus the normal in-Isaac active-stage preflight before
  any candidate-scene authoring.

## 2026-07-31T00:58:33Z — Adopted dual-channel MCP preflight

- Objective: execute the user-specified read-only Claude MCP health check and
  establish the exact preflight boundary for future M1 candidate-scene work.
- Execution:
  - Ran `claude mcp list` inside the Codex sandbox; it returned MCP error
    `-32000` / `Connection closed` for `isaac-sim`.
  - Did not modify or re-register any MCP server.
  - Re-ran exactly `claude mcp list` outside the sandbox using the approved
    minimum permanent prefix rule `["claude", "mcp", "list"]`.
  - The unsandboxed command reported the user-scope `isaac-sim` stdio server as
    `Connected`.
  - Adopted the required three-part future preflight: unsandboxed Claude MCP
    list health, direct Codex Isaac MCP runtime ping, then in-Isaac active-stage,
    timeline, root-layer path, and disk-hash verification before mutation.
- Modified files: only `milestones/M1/LOG.md`; no MCP configuration, USD,
  catalog, asset, runtime script, credential, or server implementation changed.
- Isaac Sim active stage: not queried or changed in this registration-only
  check; active-stage verification remains a separate required gate immediately
  before M1-Step2 authoring.
- USD hash: not recomputed because no USD or runtime operation was performed;
  the last protected baseline evidence remains
  `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
- Acceptance result: Claude Code user-scope registration health `pass` in the
  required unsandboxed environment. This check alone does not authorize or
  validate a scene mutation.
- Failed probe: sandboxed `claude mcp list` returned `Connection closed`; this
  is classified only as an environment limitation, not a stopped server.
- Known limitation: direct Codex Isaac MCP ping and runtime stage identity must
  still be checked separately; neither is inferred from Claude CLI health.
- Commit SHA: not yet committed; M1 remains based on
  `439015e93fa47ffea75de0329d41c3dba61ab220` pending final M1 acceptance.
- Next smallest action: at the start of M1-Step2, run the remaining direct Codex
  ping and in-Isaac stage/timeline/path/hash gates, and modify only the candidate
  scene if all three preflight channels pass.

## 2026-07-31T01:02:34Z — Three-channel M1 preflight

- Objective: execute the approved ordered preflight without modifying any scene:
  unsandboxed Claude registration health, direct Codex Isaac runtime ping, then
  in-Isaac active-stage/timeline/root-layer identity and hash.
- Execution:
  - Ran `claude mcp list` outside the sandbox with the approved minimum permanent
    prefix rule `["claude", "mcp", "list"]`; `isaac-sim` reported `Connected`.
  - Called Codex `mcp__isaac_sim__get_scene_info` directly; it returned `pong`
    and the Isaac Sim Assets 6.0 root.
  - Ran one read-only Isaac Kit probe and wrote a single scratch envelope at
    `/tmp/m1_three_channel_preflight.json` containing root-layer identity, disk
    hash, dirty state, and timeline state.
- Modified files: only `milestones/M1/LOG.md` for this durable summary. No USD,
  catalog, asset, runtime script, MCP registration, credential, or server
  implementation was changed.
- Isaac Sim active stage:
  `/home/rci05/User/Lin/test_codex_claude_mcp_1/ridgeback-franka-d455-yolo-demo/scenes/ridgeback_franka_d455_demo.usd`;
  timeline stopped; root layer `dirty=true`.
- USD hashes:
  - Active protected baseline:
    `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
  - Candidate scene on disk:
    `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
- Acceptance result: registration health `pass`, direct runtime ping `pass`, and
  runtime state observation `pass`. Candidate-scene mutation gate remains
  `not ready` because the active root layer is the protected baseline rather
  than `scenes/ridgeback_franka_d455_yolo_demo.usd`.
- Failed probe: the MCP `execute_script` response wrapper again rejected the
  successful `None` return; the requested scratch envelope was present and
  complete, so this is recorded as a transport-wrapper limitation rather than a
  runtime probe failure.
- Known limitations: the active protected root remains dirty from the documented
  reopen/render state. It must not be saved. A controlled open of the candidate
  scene plus a fresh identity/hash check is required before any Step2 authoring.
- Commit SHA: not yet committed; M1 remains based on
  `439015e93fa47ffea75de0329d41c3dba61ab220` pending final acceptance.
- Next smallest action: when M1-Step2 is authorized, open the candidate scene
  without saving the current baseline session, verify the candidate root path
  and hash, then author only the factory-scene changes.

## 2026-07-31T01:14:58Z — M1-Step2 factory scene and bounded runtime acceptance

- Objective: complete the second of at most three M1 execution batches by
  composing a visible factory shelf, 20 catalog-backed objects, and Isaac
  semantic labels in the candidate scene while preserving the protected
  baseline, robot, IK target, and D455 behavior.
- Execution:
  - Re-ran the required three-channel preflight immediately before authoring:
    unsandboxed `claude mcp list` reported `isaac-sim` connected; direct Codex
    Isaac MCP returned `pong`; and the in-Isaac probe confirmed the protected
    baseline stage, stopped timeline, required robot/camera/IK prims, and exact
    baseline disk hash.
  - Measured the stopped-timeline left-camera authored world position and view
    direction, inspected the baseline golden RGB, and enumerated non-robot world
    prims before choosing a low rack placement in the established D455 view.
  - Added `scripts/build_m1_factory_scene.py`. It asserts the protected preflight
    state, authors `scenes/m1_factory_content.usda`, exports the candidate root
    from a clean anonymous disk snapshot of the baseline, validates composition,
    atomically replaces the candidate, updates scene lineage, and never saves
    the active dirty baseline root.
  - Authored a three-tier industrial rack, back panel, four posts, yellow floor
    markings, a hidden 30-asset object library, and 20 displayed instances. The
    display has four unique identities per class and maximum configured count 20.
  - Applied `SemanticsAPI:Semantics` with semantic type `class` and the fixed
    catalog label to every display and library asset root. No factory prim has
    `RigidBodyAPI`, so the first version remains static and gravity-free.
  - A single bounded read-only executor reviewed the builder. Its relative
    sublayer temp-location concern had already been corrected before execution;
    its atomic-write, composition-count, semantic, and rerun-safety suggestions
    were incorporated into the checked-in builder/validator without rerunning or
    changing the accepted scene content.
  - Added `validation/validate_m1_step2.py`. The active candidate passed root and
    content lineage, required prims, 20 display instances, four-per-class labels,
    30 library assets, resolved references, unique identities, hidden library,
    zero factory rigid bodies, and protected-baseline hash checks.
  - Opened the candidate without saving the dirty baseline. The wrapper wait was
    terminated after more than 90 seconds, then direct ping and scratch evidence
    proved the open had completed successfully with the expected candidate path,
    hash, stopped timeline, and valid `/World/Factory`.
  - Reused the reviewed runtime harness on the active candidate: 120 Play frames,
    repeated IK start, two materially different reachable poses, two D455
    captures, rigid-attachment comparison, cleanup, and disk-hash preservation.
  - Directly inspected both `rgb_left.png` captures. Both show the gray three-tier
    rack, yellow factory-zone markings, and representative objects from all five
    classes; images are non-black and the two wrist poses produce visibly
    different framing.
- Modified files:
  - `scenes/m1_factory_content.usda`
  - `scenes/ridgeback_franka_d455_yolo_demo.usd`
  - `config/object_catalog.yaml` scene-lineage fields
  - `scripts/build_m1_factory_scene.py`
  - `validation/validate_m1_step2.py`
  - `milestones/M1/LOG.md`, `milestones/M1/STATUS.md`, and
    `milestones/CURRENT.md`
  - Ignored evidence only under `outputs/captures/2026-0731-{3,4}/`, `/tmp`, and
    `validation/tmp/`; no large capture output was added to Git.
- Isaac Sim active stage:
  `/home/rci05/User/Lin/test_codex_claude_mcp_1/ridgeback-franka-d455-yolo-demo/scenes/ridgeback_franka_d455_yolo_demo.usd`;
  timeline stopped; IK subscription count after cleanup 0; root reported
  `dirty=true` from runtime/render state and was not saved.
- USD hashes:
  - Protected baseline before and after:
    `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
  - Candidate root before and after runtime acceptance:
    `9db2e99c9f121c6c28132bb2ffb09c21f6dc3005dd56ed2754ee6da8337c8e1a`.
  - Factory content layer:
    `3a425e0d14ef72dfbbd61bf8fafdbc2bc7a2ac31dc0bd5609024efc4abe2434c`.
  - Updated object catalog:
    `45b4a328384ce4a8610bde4bed397f456d1bfd03106ad7414d1040b599a020d5`.
- Acceptance result: M1-Step2 `pass`; overall M1 remains `in_progress` pending
  Step3 clean-reopen acceptance. Structural validation found 20 display objects,
  exactly four per class, 30 hidden library assets, zero missing prims, and zero
  factory rigid bodies. Runtime validation found Panda seven-joint maximum drift
  `4.23e-10 rad`, one callback after repeated start, controller error count 0,
  D455 relative translation drift `1.47e-08 m`, maximum rotation-matrix element
  drift `6.35e-08`, two unique passing captures, and unchanged candidate hash.
  Captures had non-black left RGB means `151.35` and `153.20`, 307,200 valid left
  depth pixels each, and stereo baselines `0.09504872 m`.
- Failed probes:
  - MCP `execute_script` continued to report a response-schema error when a
    successful script returned `None`; expected scratch envelopes were present
    and complete.
  - Candidate `open_stage` completed, but its wrapper session did not return
    after more than 90 seconds. The wait was terminated only after direct MCP
    ping and `/tmp/m1_step2_open_candidate.json` proved the intended stage was
    active. The open was not repeated.
  - Offline Python did not provide live Kit validation; all USD/Semantics/runtime
    checks were executed inside the connected Isaac Kit process.
- Known limitations:
  - Assets remain simple project-authored proxies with `NOASSERTION` licensing
    and `redistribution_allowed=false` until the repository owner supplies terms.
  - Some of the 20 configured objects are partially occluded or outside the two
    representative frames; the requirement is maximum configuration and scene
    visibility, not simultaneous unobstructed visibility of every instance.
  - This is not a clean-reopen claim. The currently active candidate root is
    dirty from runtime/render state and must not be saved.
- Commit SHA: not yet committed. M1 milestone commit remains deferred until the
  Step3 clean-reopen acceptance, staged-diff inspection, and final handoff entry.
- Next smallest action: M1-Step3 performs a controlled clean GUI reopen of the
  exact candidate, reruns final Play/IK/two-pose D455/visual/catalog/hash gates,
  records the accepted scene provenance, inspects the staged diff, commits and
  pushes M1, then moves `milestones/CURRENT.md` to M2 only if every gate passes.

## 2026-07-31T01:35:10Z — User-review correction for framing and Claude route

- Objective: audit the user's two Step2 review concerns without changing the
  scene: whether the documented `demo_start.py`/IKTarget workflow produced the
  intended full-rack framing, and whether Step2 used the required Claude Code
  `OPUS_TO_SONNET` executor route.
- Execution:
  - Re-read `scripts/demo_start.py`, `validation/run_baseline_acceptance.py`,
    `CLAUDE.md`, the workflow routing reference, and all three project Claude
    agent definitions.
  - Confirmed the Step2 runtime harness did not execute `demo_start.py`. It
    directly loaded `ik_controller.py` and `capture_d455.py`, then called
    `ik_follow_start()` twice and `demo_capture_setup()`.
  - Confirmed the harness did move `/World/IKTarget`, but only by two small
    translations relative to its starting pose: `(-0.04,+0.04,-0.02) m` and
    `(-0.02,-0.03,-0.005) m`. It preserved the original target quaternion in
    both poses and did not solve a new camera framing pose for the full rack.
  - Re-inspected the two reviewed captures. They prove a visible rack and
    representatives of all five classes, but they do not prove the requested
    camera pose shows the complete intended rack contents without moving the
    IKTarget.
  - Confirmed Step2 executed Claude CLI health commands such as sandbox-external
    `claude mcp list`, but did not invoke a Claude Code implementation session
    such as `claude -p --agent isaac-sim-executor ...`.
  - Confirmed `.claude/agents/isaac-sim-executor.md` exists, selects Sonnet,
    includes the Isaac workflow and `isaac-sim` MCP, and is the executor required
    by the documented `OPUS_TO_SONNET` route.
  - Confirmed the Codex internal read-only review agent used during Step2 was not
    a Claude Code session and therefore did not satisfy that route requirement.
- Modified files: only milestone continuity documents for this evidence
  correction. No USD, catalog, asset, runtime script, MCP registration, Claude
  agent definition, credential, or server implementation was changed.
- Isaac Sim active stage: not queried or changed during this document/code-path
  audit. The last verified state remains the candidate stage with timeline
  stopped and unsaved runtime/render dirty state.
- USD hash: not recomputed because no scene/runtime action occurred. The last
  verified protected baseline and candidate hashes remain `a724cd7d...` and
  `9db2e99c...`, respectively.
- Acceptance result: Step2 structural, semantic, static-physics, IK lifecycle,
  D455 rigidity, capture integrity, and hash gates remain `pass`. The documented
  operator-workflow/full-rack visual framing gate is corrected from `pass` to
  `needs_correction`; M1 cannot enter final Step3 acceptance until it is fixed
  and re-reviewed. The required Claude Code execution-route gate is also
  `needs_correction`.
- Failed probes: none in this audit. The issue is a test-design and routing gap,
  not a failed runtime probe.
- Known limitations and diagnosis:
  - Moving IKTarget by a few centimeters with an unchanged quaternion tested
    controller motion and camera rigidity, not deliberate rack framing.
  - The user's desired invariant is valid: the authored static Panda pose and
    `/World/IKTarget` should represent the same intended hand pose, so running
    `demo_start.py` does not first move the wrist away from the desired capture
    view. Technically this should be authored by solving IK for the desired
    camera/hand pose and writing consistent Panda joint state/drive targets plus
    IKTarget transform; directly setting the articulated `panda_hand` link Xform
    would be unsafe and is not the proposed correction.
  - The desired camera orientation must be solved as well as position; matching
    translation alone does not guarantee the full rack is inside the D455 view.
  - The Claude route was missed because Codex direct MCP execution and an
    internal read-only reviewer were incorrectly treated as equivalent to the
    explicit Claude Code Sonnet executor. After sandbox-external Claude MCP
    health was proven, no connection blocker remained to justify that omission.
- Commit SHA: not yet committed; no M1 acceptance commit exists.
- Next smallest action: before final M1 acceptance, delegate one bounded
  correction task to the Claude Code `isaac-sim-executor`: run the documented
  Play > `demo_start.py` workflow, determine a full-rack camera pose, author a
  consistent static Panda joint pose and IKTarget pose only in a new candidate
  revision/layer, and return evidence for Codex independent review. Do not enter
  M2 or claim Step3 pass until this gate is resolved.

## 2026-07-31T01:58:57Z — M1-Step3 Claude Code execution blocked before runtime workflow

- Objective: execute the third and final planned M1 batch with the required
  `OPUS_TO_SONNET` route: preserve the user's newly saved/reviewed pose, delegate
  the exact Play > `demo_start.py` > unchanged IKTarget > capture > stop workflow
  to Claude Code `isaac-sim-executor`, and independently review its evidence
  before any M1 acceptance or commit.
- Execution:
  - Completed the three-channel Codex preflight. Sandbox-external
    `claude mcp list` reported `isaac-sim` connected; direct Codex MCP returned
    `pong`; and an in-Isaac scratch probe confirmed the active candidate path,
    disk SHA-256 `05329ddd...`, root clean, timeline stopped, and valid factory,
    robot, and IKTarget prims.
  - Detected and preserved the user's new candidate save. The candidate changed
    from Step2 SHA `9db2e99c...` to
    `05329ddde64616b1bc05287520002e3c862942572225006232bfa76ee0b01758`;
    the protected baseline remained unchanged.
  - Found and directly inspected `outputs/captures/2026-0731-5/rgb_left.png`.
    It visibly frames the complete three-tier rack and its primary contents.
    Capture 5 passed RGB/depth/capture checks, but its recorded scene hash is
    `52d8acbf...`, proving another USD save occurred after that capture and before
    the current `05329ddd...` disk state. The two hashes are not conflated.
  - Actually launched sandbox-external Claude Code with
    `--agent isaac-sim-executor`; Sonnet session ID
    `7341215d-361d-46c6-a040-fa86d39ff670` received explicit ROUTE, OBJECTIVE,
    SCOPE, ACCEPTANCE, AUTHORITY, and STOP fields. Its authority was runtime-only,
    with no IKTarget movement, USD save, tracked edit, MCP configuration change,
    commit, or push.
  - First Claude turn stopped at its MCP permission boundary before runtime and
    created the ignored scratch record
    `validation/tmp/claude_m1_pose_validation.json`.
  - Resumed the same Claude session with a minimum tool allowlist for only
    `mcp__isaac-sim__get_scene_info`, `mcp__isaac-sim__execute_script`, and
    read-only file/hash tools. Claude confirmed `get_scene_info` worked, but
    treated the known `execute_script` response-schema error as a server defect
    instead of using the project's established scratch-envelope fallback. It
    therefore still did not execute the operator workflow.
  - Prepared a second resume of the same session with explicit instructions to
    run one self-contained Isaac payload, accept the known wrapper error, and
    read the newly timestamped scratch envelope. The required unsandboxed command
    approval was rejected, so the command was not started and no workaround was
    attempted.
- Modified files: `milestones/M1/LOG.md`, `milestones/M1/STATUS.md`, and
  `milestones/CURRENT.md` only. Claude created/retained the ignored
  `validation/tmp/claude_m1_pose_validation.json`. No scene, catalog, asset,
  runtime script, MCP registration/config/implementation, or credential was
  modified by this Step3 attempt.
- Isaac Sim active stage at preflight:
  `/home/rci05/User/Lin/test_codex_claude_mcp_1/ridgeback-franka-d455-yolo-demo/scenes/ridgeback_franka_d455_yolo_demo.usd`;
  root clean; timeline stopped; disk hash `05329ddd...`. Claude never reached a
  runtime stage query or Play operation. No capture 6 directory exists.
- USD hashes after the blocked attempts:
  - Protected baseline:
    `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
  - User-saved candidate:
    `05329ddde64616b1bc05287520002e3c862942572225006232bfa76ee0b01758`.
- Acceptance result: `blocked`, not `fail` and not `pass`. Claude Code was
  genuinely invoked as required, but never completed the documented runtime
  workflow. Consequently there is no Claude-origin demo_start result, startup
  snap measurement, unchanged-target proof, capture 6, cleanup proof, clean
  reopen acceptance, M1 commit, or push.
- Failed probes:
  - Claude attempt 1: MCP tools denied by Claude session permissions.
  - Claude attempt 2: minimum MCP permissions succeeded for ping, but Claude
    stopped on the known execute-script wrapper schema error and its own
    `dontAsk` Write/Edit denial rather than consuming scratch evidence.
  - Claude attempt 3: the command approval required to resume with explicit
    scratch-envelope instructions was rejected before process creation.
- Known limitations:
  - `validation/tmp/claude_m1_pose_validation.json` contains only attempt-1
    permission evidence and is stale for attempt 2; it must not be cited as a
    runtime acceptance record.
  - Capture 5 visually supports the user's framing review but was produced at
    scene hash `52d8acbf...`, not the current `05329ddd...`; a final capture on
    the exact current hash remains required.
  - The catalog's Step2 candidate lineage hash remains historical until the
    current user-saved candidate passes final acceptance.
- Commit SHA: none. No files were staged, committed, or pushed.
- Next smallest action: with user approval, resume the same Claude session
  `7341215d-361d-46c6-a040-fa86d39ff670` using the already defined minimum MCP
  allowlist and explicit scratch-envelope fallback. Only after Claude completes
  the public workflow may Codex inspect the new image/evidence, run final
  clean-reopen gates, update lineage, and decide M1 acceptance.

## 2026-07-31T02:41:22Z — Codex/Claude execution-contract migration

- Objective: replace the fragile Codex-to-Claude session-resume workflow with a
  durable contract in which Codex and the user define one milestone task,
  Claude Code Opus executes it and may delegate bounded subtasks to Sonnet, and
  Codex independently reviews acceptance and owns the default commit/push.
- Task and contract changes:
  - Added the milestone-independent startup contract at
    `docs/CLAUDE_OPUS_BOOTSTRAP.md`.
  - Added the exact current work order at `milestones/M1/tasks/M1-S3.md`.
  - Updated `milestones/CURRENT.md` to identify exactly one ready task and to
    retire the instruction to resume Claude session
    `7341215d-361d-46c6-a040-fa86d39ff670`.
  - Updated `AGENTS.md`, `CLAUDE.md`, `PROJECT_PROFILE.md`, `README.md`, the
    milestone continuity instructions, workflow routing reference, and Claude
    Opus agent definition so Opus controls optional Sonnet delegation while
    Codex remains the final reviewer.
  - Updated `milestones/M1/STATUS.md`: M1 remains `in_progress`, not accepted;
    `M1-S3` is ready and the remaining gate is exact-hash public-workflow
    evidence rather than evidence provenance from a particular model/session.
- Existing M1 checkpoint preserved:
  - Protected baseline SHA-256 remains `a724cd7d...`.
  - User-reviewed candidate SHA-256 remains `05329ddd...`.
  - Factory content was normalized to a single final newline for deterministic
    regeneration; its checkpoint SHA-256 is `4cb30f78...` and the catalog
    lineage was updated accordingly.
  - The catalog hash after that lineage update is `97cdeb31...`.
  - Thirty project-authored `.usda` object assets remain present.
- Verification:
  - New prompt/task paths and current-task pointer exist.
  - M1 Python files pass `py_compile`; `git diff --check` passes.
  - The dependency-free Step1 validator now predictably reports only its stale
    Step1 premise that the evolved candidate must still be byte-identical to the
    baseline. This is retained as a validator-scope limitation, not called an
    M1 failure.
  - The Step2 validator cannot run in system Python because `omni` is available
    only inside Isaac Kit; no live runtime or USD mutation was authorized or
    performed for this contract migration.
- Failed probe: one read-only `rg` cross-reference command used Markdown
  backticks in a shell pattern, causing harmless command substitution messages;
  no file or runtime state changed, and the checks were rerun with literal
  patterns.
- Commit SHA: pending the staged-diff inspection requested by the user.
- Next action: commit this honest M1 in-progress checkpoint, then start a new
  Claude Code Opus conversation with `docs/CLAUDE_OPUS_BOOTSTRAP.md`; Claude
  executes only `M1-S3`, appends this log, and stops for Codex review.
