# Evidence Policy

Use three evidence levels.

## Scratch

Store probes, retries, and failures under `outputs/` or `validation/tmp/`. Ignore them in Git. Reuse or replace a logical operation's result instead of creating `v2`, `v3`, `final`, and `final2` files at repository root.

## Capture

Use one unique directory per operator capture. Keep:

- one compact capture status record;
- the complete measurement report when measurement is a product requirement;
- raw images and depth needed to reproduce claims;
- an optional summary derived from the same measurements.

A summary is not a second detector or independent evidence source.

## Release

Commit one reviewed `validation/release_acceptance.json` and only the minimum golden media needed to explain the result. Include:

- schema version, run ID, UTC timestamp, and final result;
- exact active-stage path and SHA-256;
- Isaac Sim version and physics backend when available;
- timeline and callback state;
- relevant numeric checks with observed values, thresholds, and pass/fail;
- failures and known limitations;
- relative paths to selected artifacts.

Do not cite a superseded scratch result as release authority. Do not copy complete historical metrology runs into a new demo project.

## Efficiency metrics

For workflow experiments, consolidate counters into the release or run summary:

- user clarification rounds;
- Codex handoffs;
- Opus delegations;
- Sonnet tasks;
- MCP calls and retries;
- acceptance runs;
- first call that produced visible useful output.

Count these separately; “number of commands” is otherwise ambiguous.
