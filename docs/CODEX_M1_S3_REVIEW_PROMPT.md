# Codex Review Prompt — Complete M1-S3 Under the New Contract

Use this prompt after Claude Code Opus has executed the current `M1-S3` task,
appended `milestones/M1/LOG.md`, and returned control to the user. This prompt is
for Codex review; it must not launch or resume the obsolete Claude session.

## Prompt to give Codex

```text
Act as the project architect and final acceptance reviewer for M1-S3 in:

/home/rci05/User/Lin/test_codex_claude_mcp_1/ridgeback-franka-d455-yolo-demo

Use the new Codex→Claude Opus execution contract. Claude has been responsible
for executing the current task and appending the milestone log; Codex is now
responsible for independent review, gap analysis, status/current ownership, and
the commit/push decision.

Do not resume Claude session `7341215d-361d-46c6-a040-fa86d39ff670` and do not
launch another Claude task before reviewing the current evidence.

First, completely read:

1. AGENTS.md
2. CLAUDE.md
3. README.md
4. PROJECT_PROFILE.md
5. docs/CLAUDE_OPUS_BOOTSTRAP.md
6. milestones/CURRENT.md
7. milestones/AGENT_HANDOFF.md
8. milestones/M1/STATUS.md
9. milestones/M1/LOG.md, including the newest Claude execution entry
10. milestones/M1/tasks/M1-S3.md
11. .agents/skills/isaac-sim-mcp-workflow/SKILL.md and every required reference
12. validation/tmp/claude_m1_s3_result.json if it exists
13. every capture, scratch envelope, and changed file cited by the newest log

Treat the current filesystem, Git state, USD disk hashes, and live Isaac Sim
runtime as authoritative. Do not trust a pass label without direct evidence.

Review procedure:

1. Identify the newest Claude M1-S3 LOG entry and confirm it cites the exact
   current task. If no new Claude execution entry exists, stop and report that
   M1-S3 has not been executed; do not fabricate a review.
2. Inspect `git status`, the complete diff, untracked files, and current HEAD.
   Preserve all user/Claude changes. Confirm Claude stayed within M1-S3
   authority: ignored scratch/capture output plus append-only M1 LOG, with no
   unauthorized USD, catalog, script, STATUS, CURRENT, MCP-config, commit, or
   push changes.
3. Verify disk SHA-256 values:
   - protected baseline must remain
     `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`;
   - candidate for the Claude run must be
     `05329ddde64616b1bc05287520002e3c862942572225006232bfa76ee0b01758`;
   - factory content must match the current task;
   - capture metadata must cite the same candidate hash before and after.
4. Review `validation/tmp/claude_m1_s3_result.json` for freshness, stage path,
   timeline, errors, traceback, checks, hashes, and cleanup. Do not cite stale
   `claude_m1_pose_validation.json` or Capture 5 as M1-S3 evidence.
5. Inspect the new RGB image and depth preview directly. Verify useful full-rack
   framing and representative contents. Inspect raw depth arrays numerically,
   including finite positive pixels, shape, range, and stereo baseline.
6. Confirm the public operator path was actually used:
   Play → execute `scripts/demo_start.py` → do not manually move IKTarget →
   public `demo_capture()` → public `demo_stop()` → stop timeline.
   Loading `ik_controller.py` and `capture_d455.py` privately is not a substitute.
7. Check the observed startup invariants:
   - IKTarget translation/orientation before and after startup;
   - Panda seven-joint startup delta and visible snap assessment;
   - panda_hand and D455 camera poses;
   - exactly one IK callback;
   - controller error count zero.
8. Independently use the Codex Isaac MCP and live Isaac Sim runtime for the
   smallest checks needed to validate active-stage identity, callback cleanup,
   stopped timeline, root dirty state, required prims, and any disputed Claude
   observation. Before every execute_script call, print the exact code. Account
   for the known response-wrapper error by reading a fresh scratch envelope.
9. Run the appropriate M1 structural/catalog validation inside Isaac Kit where
   `omni`/`pxr` are available. Do not treat the Step1 validator's historical
   byte-identical-candidate assumption as a final M1 gate after Step2 authoring.
10. Confirm both protected and candidate USD disk hashes remain unchanged after
    review. Never save runtime/session state into either USD.

Classify every M1-S3 and remaining M1 gate as pass, fail, blocked, or not_run.
Model provenance is not an acceptance gate; observable project evidence is.

Decision:

- If evidence is incomplete, inconsistent, visually inadequate, or outside
  tolerance, do not silently implement a correction. Append a Codex review
  entry to `milestones/M1/LOG.md`, explain the exact gap to the user, and discuss
  the next product/behavior instruction. Only after that discussion, author a
  new task file for Claude and update CURRENT/STATUS accordingly.
- If M1-S3 and all remaining M1 gates pass, update any final candidate/catalog
  lineage and compact M1 acceptance evidence, append the Codex review and M1
  handoff entries, mark M1 complete, and point CURRENT to the next user-approved
  task. Inspect the staged diff, commit the accepted M1 work, record the full
  commit SHA in the log, and push to origin/main.
- Do not enter or execute M2 merely because M1 passes. The next executable task
  must first be discussed with the user and authored by Codex.

Final response to the user must lead with:

1. whether M1-S3 passed;
2. whether M1 as a whole is complete;
3. the observable result in Isaac Sim;
4. the remaining distance from the user's intended factory D455/YOLO project;
5. any additional Claude task that should be discussed;
6. commit/push status when applicable.
```

## Short invocation

After Claude finishes, the user may tell Codex:

```text
Read `docs/CODEX_M1_S3_REVIEW_PROMPT.md` completely and perform that independent
M1-S3 review. Do not launch a new Claude task before reporting the current gap.
```
