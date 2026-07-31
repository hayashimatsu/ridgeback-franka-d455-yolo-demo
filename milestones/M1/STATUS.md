# M1 Status — Factory Scene and Object Catalog

- Owner: Agent 1
- State: `in_progress`; current task `M1-S3` is `ready`
- Entry gate: `pass`; M0 clean-reopen baseline check passed at commit
  `5ac9552f273ca018feef9adaf8b7e1cda6cc1dcb`.
- Objective: create `scenes/ridgeback_franka_d455_yolo_demo.usd` without
  modifying the imported baseline; add the factory shelf and at least six
  assets for each of five classes.
- Step1 result: `pass`; a byte-identical candidate revision, 30 project-authored
  USD proxy assets, the five-class object catalog, and a repeatable validator
  exist. Each class has three train, two validation, and one held-out identity.
- Step2 technical result: `pass` for factory composition, catalog identities,
  SemanticsAPI labels, zero factory rigid bodies, Play/IK/two-pose D455/capture,
  and USD immutability.
- Step2 review correction: `needs_correction` for the documented
  `demo_start.py` operator workflow, deliberate full-rack camera framing, and
  consistent authored static Panda/IKTarget pose. M1 is not accepted.
- Protected baseline SHA-256:
  `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
- Candidate initial SHA-256:
  `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
- Candidate Step2 SHA-256:
  `9db2e99c9f121c6c28132bb2ffb09c21f6dc3005dd56ed2754ee6da8337c8e1a`.
- User-saved reviewed candidate SHA-256:
  `05329ddde64616b1bc05287520002e3c862942572225006232bfa76ee0b01758`.
- Factory content SHA-256:
  `4cb30f7854f486bd77f83b5bd47530ce2d920f006d82bcbb82f3047b69a5ff49`.
- Catalog: `config/object_catalog.yaml`; Step1 validator passed all catalog,
  hash, split, and 31-layer USD parse checks.
- Required evidence: new-stage provenance, asset source and license records,
  clean Play stability, IK and D455 preservation, and accepted object catalog.
- Process blocker resolution: the requirement to resume a specific Claude
  Sonnet session is retired. Product acceptance depends on exact-hash evidence,
  not which model originated it. Claude Code Opus now executes the current
  Codex-authored task and may delegate bounded work to Sonnet.
- Remaining evidence: public `demo_start.py` workflow on the exact current
  candidate hash, unchanged IKTarget/startup-snap proof, a new capture, cleanup,
  clean GUI reopen, final visual/hash gates, staged-diff inspection, compact
  provenance, commit/push, and handoff.
- Current task: `milestones/M1/tasks/M1-S3.md`.
- Next action: start a new Claude Code Opus conversation with
  `docs/CLAUDE_OPUS_BOOTSTRAP.md`; execute only `M1-S3`, append this milestone
  log, and stop for Codex review.
