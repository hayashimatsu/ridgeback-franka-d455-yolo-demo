# Agent Handoff Contract

The three agents own sequential segments, not concurrent branches of the same
USD workflow.

## Agent 1 — M1 to M3

- M1: create and validate a new factory-shelf USD revision and object catalog.
- M2: implement Replicator RGB, instance-mask, and YOLO-segmentation dataset
  generation.
- M3: audit dataset quality and freeze train, validation, held-out, stress, and
  negative splits.
- Entry gate: M0 clean-reopen baseline check passes.
- Handoff output: accepted scene provenance, immutable asset taxonomy, dataset
  manifest, split identities, label audit, known data limitations, and exact
  commit SHA.

## Agent 2 — M4 to M5

- M4: create the isolated training environment, train and compare compact YOLO
  segmentation models, and freeze a reproducible model artifact.
- M5: integrate real-time inference, mask-depth fusion, world coordinates,
  visible 3D extent, and unknown-surface behavior.
- Entry gate: Agent 1 records M3 as accepted and provides a stable dataset
  manifest plus split hashes.
- Handoff output: model and dataset hashes, per-class metrics, inference backend,
  runtime API, coordinate checks, performance evidence, limitations, and commit
  SHA.

## Agent 3 — M6 to M7

- M6: integrate the dockable GUI, lifecycle functions, and auditable capture.
- M7: run stress, performance, clean-reopen, visual, provenance, and release
  acceptance gates.
- Entry gate: Agent 2 records M5 as accepted with a stable runtime API and model
  artifact.
- Handoff output: operator runbook, final candidate provenance, representative
  reviewed media, compact release acceptance, known limitations, and release
  commit SHA.

## Coordination rules

- Do not begin a later segment on provisional outputs from an earlier agent.
- Never edit the imported baseline USD; all scene work uses a new revision.
- Do not run two owners against the same USD, dataset manifest, model artifact,
  or runtime entry point at the same time.
- A blocked gate stays blocked until direct evidence resolves it; downstream
  work does not redefine or bypass the gate.
- Each agent must append a final handoff entry to its last milestone log before
  the next agent begins.
