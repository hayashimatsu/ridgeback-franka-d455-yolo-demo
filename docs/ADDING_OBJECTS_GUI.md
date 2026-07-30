# Adding Objects and Wrist Accessories in the GUI

This is a maintenance reference for a later guided session. The safe procedure
depends on what the new object is intended to do.

## Choose the object role first

| Role | Example | Recommended model |
|---|---|---|
| Scene decoration | table, box, inspection part | Add it under `/World`; use normal transform tools |
| Visual wrist accessory | camera housing, marker, passive sensor | Add a mount Xform under `panda_hand`; keep the accessory non-rigid so it inherits the hand transform |
| Physical wrist payload | tool whose mass/contact must affect the arm | Use a rigid body with mass and a correctly configured Physics Fixed Joint |
| Grasped object | part picked up and released during the demo | Keep it under `/World`; attach/detach it at runtime with a grasp joint or gripper workflow |

Do not mix the visual-accessory and physical-payload models. An independently
enabled rigid body parented under the hand is not automatically a rigid mount.

## GUI-first workflow

1. Stop the timeline.
2. Use **File > Save As** and create a new scene revision in this repository.
3. Add or reference the object in the Stage tree.
4. Place it with the Move and Rotate gizmos while inspecting front, side, and
   top views.
5. Decide whether the object needs physics. Do not add Rigid Body merely because
   the object is attached to a robot.
6. Press Play and inspect the result before saving again.

For ordinary scene objects, these GUI steps are usually sufficient. A small
automation script becomes worthwhile when placement must be repeated, a numeric
transform must be exact, many objects are involved, or validation must be
automated.

## Wrist-mounted visual accessory

Create an Xform below `/World/ridgeback_franka/panda_hand`, place the referenced
asset below that Xform, and adjust its local transform. If the referenced asset
contains an independently enabled `RigidBodyAPI`, disable that rigid body for a
sensor-style kinematic attachment. This is the model used by the demo D455.

Validate by moving IKTarget to two reachable poses and confirming that the
hand-to-accessory relative transform does not change.

## Physical wrist payload

A payload whose mass or collision must affect the arm needs a different model:

- enable one rigid body on the payload root;
- assign a realistic mass and collision representation;
- create a Physics Fixed Joint connecting the correct hand rigid body to the
  payload rigid body;
- do not also disable that payload rigid body;
- start with conservative joint drives and test for snapping or instability.

The relative joint frames should be derived from the actual placement rather
than guessed. This is a good point to use a small validation script even when
the initial placement was done in the GUI.

## Minimum acceptance

- The original demo scene remains unchanged.
- The new revision opens directly.
- Play causes no snap or falling object.
- The accessory follows the hand across two poses.
- The D455 view and IK target remain usable.
- If physics was added, mass, collision, and joint relationships are explicit.
- Only the accepted new revision becomes the manifest default.
