# Acceptance Gates

Apply only gates relevant to the claim, but never weaken a project-specific gate.

## Any live operation

- active stage matches `PROJECT_PROFILE.md`;
- no unexpected callback or subscription duplication;
- errors and timeouts are disclosed;
- temporary state is restored;
- unauthorized files or prims are unchanged.

## Articulation or IK

- Play does not cause an unintended snap from the authored pose;
- only intended DOFs move;
- a reachable target satisfies position and orientation tolerances;
- base, gripper, or other excluded DOFs remain unchanged;
- lifecycle start, duplicate-start, stop, and restart behave as specified.

## Rigid sensor attachment

- test at least two materially different reachable arm poses;
- compare hand-to-sensor relative translation and orientation;
- evaluate against explicit numeric drift thresholds.

## Camera and capture

- RGB frames are non-black and visually inspected;
- raw depth contains valid finite values in the expected range;
- stereo baseline meets the project tolerance;
- left/right images are not stale duplicates when a stereo distinction is claimed;
- temporary targets or markers are restored after capture;
- a second unlabeled capture cannot overwrite the first;
- the root USD hash is unchanged by runtime-only capture.

## Release

- reopen the candidate in a clean GUI session;
- run the documented operator workflow, not a private substitute;
- consolidate results in one acceptance record;
- state known limitations and any untested boundary;
- stop controllers and leave the timeline in the documented final state.
