# Live GUI Demo Runbook

## Before the presentation

1. Start Isaac Sim and open `scenes/ridgeback_franka_d455_demo.usd`.
2. Confirm the Stage tree contains `/World/ridgeback_franka` and
   `/World/IKTarget`.
3. Press **Play**.
4. Open **Window > Script Editor**.
5. Open `scripts/demo_start.py` and press **Ctrl+Enter** once.
6. Confirm the printed result contains `"status": "ready"`.

The startup script is safe to run again. It removes the previous IK callback
before starting a replacement, so duplicate subscriptions do not accumulate.

## Aim the camera

1. Select `/World/IKTarget` in the Stage tree.
2. Use the Move or Rotate gizmo.
3. Move in small steps of roughly 2–5 cm and allow the hand to settle.
4. Do not drag `panda_hand` directly. It is a PhysX articulation link, so its
   transform is controlled by the arm joints.

If the target is outside the dexterous workspace, the controller may stop at the
nearest stable pose. Move the target closer rather than repeatedly restarting
the controller.

## Take a snapshot

Use the Script Editor console:

```python
demo_capture()
```

The command waits briefly for IK convergence, temporarily hides IKTarget,
captures the three D455 RGB cameras and depth products, restores the target, and
prints the unique output directory.

The capture writes one complete, color-independent `measurements.json` report.
It records depth-continuous visible surfaces from near to far. `summary.json`
is only a smaller view of those same records; it is not a second measurement.
To rebuild both files for a specific range after capture, run for example:

```python
demo_measure_capture(
    demo_capture_status()["output_directory"],
    minimum_depth_m=1.0,
    maximum_depth_m=5.0,
)
```

This range limits measurement candidates; it does not identify object classes.
A wall that fills the image is retained as a large border surface. Two touching
objects at nearly identical depth may still merge and require a GUI ROI or a
semantic/instance detector.

For every surface, `representative_point` is the valid region pixel nearest the
2D mask centroid. It is a repeatable visible-surface sample, not the object
center. Use `visibility.bbox_px` for image coverage,
`visible_surface_extent_m` for camera/world 3D bounds, and
`surface_depth_profile_m` for minimum, robust percentiles, median, and maximum
depth. For a curved or otherwise non-planar surface, load
`depth_region_labels.npy`, select its `label_value`, and back-project the
matching pixels from `depth_axial_left.npy`; this retains the measured scene
depth instead of forcing the object into a plane model.

For routine GUI checking, open `summary.json` first. Its
`visible_targets_near_to_far` list contains only the rank, geometric type hint,
camera-to-visible-surface distance, and measured camera/world coordinates. The
distance is the Euclidean norm of that exact camera-space point. A
plane candidate also includes a `constant_world_axis`; compare that surface
coordinate with the matching GUI surface, not directly with the prim's center
Translate value. For example, a Cube centered at `X=5.115 m` with `0.1 m`
thickness has a front surface near `X=5.065 m`.

For a rotated plane, use `plane.normal_world_unit`, `plane.point_world_xyz_m`,
and its equation instead. `constant_world_axis` is present only when the measured
normal is closely aligned with world X, Y, or Z.

Open `rgb_left_annotated.png` and `depth_preview_annotated.png` together. The
RGB image labels each representative sample as `T3 (u,v)`, with the origin at
the top-left. The depth image places `T3 <depth> m` at that same pixel; the
value is axial Z-forward depth from `distance_to_image_plane`, not oblique
camera-to-surface range. The same crosshair must land on the same visible
surface in both images.
`region_overlay.png` displays reported targets only and uses the same `T#`
labels as the annotated RGB and depth images. Known floor regions remain in
`depth_region_labels.npy` as raw audit evidence but are excluded from the
target JSON array and all operator overlays. The JSON border flag uses a
two-pixel margin because surface-normal estimation cannot classify the exact
outer image pixel reliably.
The exclusion is sensor-derived: a candidate must be a large horizontal plane
and its measured median world Z must be within `0.15 m` of zero. A horizontal
object at another height remains a reported target.

An optional label can be added, but is never required:

```python
demo_capture("side-view")
```

Output is stored in:

```text
outputs/captures/<YYYY-MMDD-sequence>[-optional-label]/
```

For example, three unlabeled captures on July 28, 2026 are stored as
`2026-0728-1`, `2026-0728-2`, and `2026-0728-3`. The files inside every
snapshot directory use stable names. Uniqueness comes from the directory name,
not from asking the operator to invent a filename.

## Continue or stop

- Continue aiming and call `demo_capture()` again for another snapshot.
- Inspect the latest result with `demo_capture_status()`.
- End the demo with `demo_stop()` and then stop the timeline.
- Do not save the USD after an interactive demo unless the intention is to
  author a new scene revision.

## Troubleshooting

### The arm does not move

Check that the timeline is playing, then run:

```python
ik_follow_status()
ik_follow_subscription_count()
```

The subscription count should be `1`. Re-run `scripts/demo_start.py` if it is
zero.

### A capture reports `fail`

Open that run's `capture.json` and inspect `failures` first. Common causes are a
black camera frame, no valid depth, an incorrect stereo baseline, or an IK
target that did not converge before the timeout. Failed output is retained in
`outputs/` for diagnosis but is not release evidence.

### The yellow target appears in the image

Use the default `demo_capture()` call. Do not change the target material to
transparent; transparent geometry may still occlude RTX depth. The capture
script uses session-layer visibility and restores it in a `finally` block.

## Release acceptance

Before a tagged demo release, perform a clean reopen and verify:

1. Play causes no visible arm snap.
2. IK subscription count is exactly one.
3. Two reachable target moves visibly change the camera viewpoint.
4. The D455 remains fixed to the hand across both poses.
5. Two consecutive unlabeled `demo_capture()` calls create different folders.
6. Both captures contain non-black left, right, and color images plus valid raw
   depth.
7. `ik_settle.settled` is true; an IK timeout makes the capture fail.
8. The measured stereo baseline is `0.095 m ± 0.002 m`.
9. IKTarget is visible again after each capture.
10. The demo USD hash is unchanged by the complete operation.
