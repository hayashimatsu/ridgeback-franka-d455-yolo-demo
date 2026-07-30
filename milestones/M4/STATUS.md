# M4 Status — YOLO Training and Model Selection

- Owner: Agent 2
- State: `pending`
- Entry gate: Agent 1 accepts M3 and hands off stable dataset hashes.
- Objective: train reproducible compact YOLO segmentation candidates and select
  the fastest model that satisfies project accuracy gates.
- Required evidence: pinned environment, model and dataset hashes, per-class
  precision and recall, mAP, held-out results, latency comparison, and artifact
  license.
- Next action: wait for Agent 1 handoff.
