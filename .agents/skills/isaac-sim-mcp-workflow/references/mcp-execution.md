# Isaac Sim MCP Execution

## Efficient order

1. Confirm `isaac-sim` is connected.
2. Confirm the active stage path and root layer.
3. Inspect authored prim structure, attributes, camera offsets, and expected baseline.
4. Confirm timeline and callback/subscription state.
5. Read runtime articulation and Xform state while Play is active.
6. Exercise the smallest reachable motion needed to test the claim.
7. Initialize render products once, warm them deliberately, then capture.
8. Run expensive image, depth, stereo, or metrology checks only after geometry and state pass.

## Script design

- Prefer a checked-in bootstrap with idempotent functions such as `start`, `status`, `capture`, and `stop`.
- Make startup remove or reuse earlier callbacks so duplicate subscriptions do not accumulate.
- Dynamically resolve articulation DOFs and command only the intended joints.
- Return small structured summaries. Save raw arrays as `.npy` or images rather than embedding them in JSON.
- When an MCP response channel is unreliable, write one scratch result envelope per logical operation, not one permanent file per observation.
- Include `status`, `error`, `traceback`, stage identity, timeline state, and the measurements required for the current decision.

## Runtime versus authored state

Authored USD transforms may describe the pre-Play pose after physics or IK moves. While the timeline is playing, obtain moving robot and camera world poses from runtime articulation/Xform APIs. Use authored USD state for offline structure checks and stopped-timeline fallbacks.

## Safe persistence

- Treat the current release USD as immutable unless the user explicitly authorizes replacing it.
- For a scene change, create a new revision, reopen it cleanly, validate it, and only then update a manifest or default pointer.
- Do not save session-layer visibility, render products, live drive targets, or temporary diagnostic objects into the root layer by accident.
- Hash the active root layer before and after runtime-only capture.
