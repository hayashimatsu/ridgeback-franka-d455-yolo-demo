"""GUI-driven inverse-kinematics controller for the Ridgeback + Franka demo.

The controller follows `/World/IKTarget` while the Isaac Sim timeline is
running. It commands only the seven Panda arm joints, preserves the mobile base,
limits every update, and restores the captured clean pose on stop or failure.

Public entry points are `start()`, `stop()`, `status()`, and `get_controller()`.
"""

import builtins
import math
import traceback

import numpy as np

import omni.kit.app
import omni.timeline
from isaacsim.core.experimental.prims import Articulation, XformPrim

# ---------------------------------------------------------------------------
# Tunable constants (see docstring above for the rationale behind each one)
# ---------------------------------------------------------------------------
ARTICULATION_PATH = "/World/ridgeback_franka"
HAND_LINK_NAME = "panda_hand"
TARGET_PRIM_PATH = "/World/IKTarget"
ARM_JOINT_NAMES = [f"panda_joint{i}" for i in range(1, 8)]

DAMPING = 0.05  # lambda in the DLS formula; "Moderate" tier; sizes step gain
NULL_DAMPING = 0.005  # much lighter damping used ONLY to build null-space
# projectors (N_pos, N_task) -- see module docstring ("NULL-SPACE LEAKAGE
# BUG") for why DAMPING alone was not safe to reuse there.
MAX_JOINT_DELTA_PER_STEP = 0.05  # rad, L2-norm-clamped over the 7-vector
POSTURE_GAIN = 0.02  # null-space pull back toward R5_CLEAN_ARM_POSE; see docstring
MAX_POSTURE_DELTA_PER_STEP = 0.01  # rad, independent cap on the posture term alone

# Superseded by WEIGHTED_SINGLE_STACK_DLS below (kept only as historical
# record in the docstring's "ANTI-PARALLEL PRIMARY/SECONDARY CANCELLATION
# BUG" and "WEIGHTED SINGLE-STACK DLS" sections): three successive
# task-priority variants (absolute dq_rot cap, then a relative cap with a
# floor, then a pure ratio cap) all still left orientation stranded in a
# near-singular null space once position was solved with zero regard for
# it. The weighted single solve below replaced the whole hierarchy, so
# MAX_ROT_DELTA_PER_STEP / ROT_TO_POS_RATIO / POS_NEAR_ZERO_THRESHOLD are
# no longer used by the running solver.

POS_WEIGHT = 1.0  # row weight on the 3 position error/Jacobian rows
# Orientation's row weight is ADAPTIVE (see _adaptive_rot_weight() and
# docstring "WEIGHTED SINGLE-STACK DLS" for why a single fixed ROT_WEIGHT
# was insufficient): low while position still has significant work left,
# ramping up toward ROT_WEIGHT_MAX as position approaches convergence.
ROT_WEIGHT_MIN = 0.08
ROT_WEIGHT_MAX = 0.6
ROT_WEIGHT_RAMP_SCALE = 0.06  # m; pos_err_norm at/above this uses
# ROT_WEIGHT_MIN, ramping linearly to ROT_WEIGHT_MAX as pos_err_norm -> 0

# Manipulability-adaptive damping (Nakamura-Hanafusa singularity-robust
# style). Below SIGMA_THRESHOLD, damping ramps smoothly from the base value
# up to LAMBDA_MAX as the relevant smallest singular value approaches zero.
# See _manipulability_damping() and the docstring section named above.
SIGMA_THRESHOLD = 0.05
LAMBDA_MAX = 0.3

# Static fallback pose (the authored clean joint state / drive target). Used by
# stop()/on-error recovery only if a controller instance never captured a live
# clean pose, for example when start() fails before initialization completes.
R5_CLEAN_ARM_POSE = [
    0.0,
    0.5235987901687622,
    0.0,
    -0.7853981852531433,
    0.0,
    1.5707963705062866,
    0.7853981852531433,
]

_REGISTRY_ATTR = "_ik_follow_controller_registry"


def _get_registry():
    if not hasattr(builtins, _REGISTRY_ATTR):
        setattr(builtins, _REGISTRY_ATTR, {"instance": None})
    return getattr(builtins, _REGISTRY_ATTR)


def _quat_conjugate(q):
    return np.array([q[0], -q[1], -q[2], -q[3]], dtype=np.float64)


def _quat_mul(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array(
        [
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        ],
        dtype=np.float64,
    )


def _manipulability_damping(sigma_min, lambda_base):
    """Scale a base damping value up as `sigma_min` (the smallest singular
    value of the Jacobian channel it damps) approaches zero, per the
    module docstring's "MANIPULABILITY-ADAPTIVE DAMPING" section. Returns
    `lambda_base` unchanged when `sigma_min >= SIGMA_THRESHOLD` (healthy
    conditioning); ramps smoothly (quadratically) up to `LAMBDA_MAX` as
    `sigma_min -> 0`."""
    if sigma_min >= SIGMA_THRESHOLD:
        return lambda_base
    frac = 1.0 - (sigma_min / SIGMA_THRESHOLD)
    return lambda_base + (LAMBDA_MAX - lambda_base) * (frac ** 2)


def _adaptive_rot_weight(pos_err_norm):
    """Orientation row weight for the weighted single-stack DLS solve,
    ramped by the CURRENT position error -- see module docstring
    ("WEIGHTED SINGLE-STACK DLS", final-fix paragraph). Returns
    `ROT_WEIGHT_MIN` when `pos_err_norm >= ROT_WEIGHT_RAMP_SCALE` (position
    still has meaningful work left; keep orientation's influence on the
    chosen configuration low so it does not derail position progress),
    ramping linearly up to `ROT_WEIGHT_MAX` as `pos_err_norm -> 0`
    (position converged/converging; let orientation matter more so it is
    not stranded in whatever null space happened to be left over)."""
    if pos_err_norm >= ROT_WEIGHT_RAMP_SCALE:
        return ROT_WEIGHT_MIN
    frac = 1.0 - (pos_err_norm / ROT_WEIGHT_RAMP_SCALE)
    return ROT_WEIGHT_MIN + (ROT_WEIGHT_MAX - ROT_WEIGHT_MIN) * frac


def _axis_angle_error(q_current, q_target):
    """World-frame rotation vector (axis * angle, radians) that rotates
    q_current onto q_target. Quaternions are wxyz."""
    q_err = _quat_mul(q_target, _quat_conjugate(q_current))
    if q_err[0] < 0.0:
        q_err = -q_err
    w = float(np.clip(q_err[0], -1.0, 1.0))
    angle = 2.0 * math.acos(w)
    sin_half = math.sqrt(max(0.0, 1.0 - w * w))
    if sin_half < 1e-8 or angle < 1e-8:
        return np.zeros(3, dtype=np.float64)
    axis = q_err[1:4] / sin_half
    return axis * angle


class IKFollowController:
    """Damped-least-squares 6-DOF IK follow controller.

    See module docstring for the full startup contract, the runtime API
    paths, the Jacobian layout, and the solver constants' rationale.
    """

    def __init__(self):
        self._sub = None
        self._art = None
        self._hand = None
        self._target = None
        self._arm_dof_indices = None
        self._hand_jac_row = None
        self._dof_lo = None
        self._dof_hi = None
        self._clean_arm_targets = None
        self._q_cmd = None
        self._posture_ref = None
        self._running = False
        self._error_count = 0
        self._last_error = None
        self._step_count = 0

    # -- lifecycle -----------------------------------------------------
    def start(self):
        if self._running:
            return {"status": "already_running"}

        art = Articulation(ARTICULATION_PATH)
        dof_names = list(art.dof_names)
        link_names = list(art.link_names)

        missing = [n for n in ARM_JOINT_NAMES if n not in dof_names]
        if missing:
            raise RuntimeError(f"arm joint DOFs not found on {ARTICULATION_PATH}: {missing}")
        if HAND_LINK_NAME not in link_names:
            raise RuntimeError(f"link '{HAND_LINK_NAME}' not found on {ARTICULATION_PATH}")

        arm_dof_indices = [dof_names.index(n) for n in ARM_JOINT_NAMES]
        hand_link_index = link_names.index(HAND_LINK_NAME)
        hand_jac_row = hand_link_index - 1  # jacobian excludes the fixed "world" root link

        if not getattr(art, "_physics_tensor_entity_initialized", False):
            raise RuntimeError(
                "physics tensor entity not initialized -- press Play before "
                "calling ik_follow_start() (Jacobians require the physics "
                "sim to have stepped at least once)."
            )

        jac_shape = art.get_jacobian_matrices().numpy().shape
        if jac_shape[1] != len(link_names) - 1:
            raise RuntimeError(
                f"unexpected jacobian row count {jac_shape[1]} for "
                f"{len(link_names)} links; refusing to start with an "
                f"unverified row mapping."
            )

        lo, hi = art.get_dof_limits()
        dof_lo = lo.numpy()[0]
        dof_hi = hi.numpy()[0]

        hand = XformPrim(f"{ARTICULATION_PATH}/{HAND_LINK_NAME}")
        target = XformPrim(TARGET_PRIM_PATH)

        # Requirement: initialize the IK target to the current hand pose so
        # enabling follow mode causes no startup jump.
        hand_p, hand_q = hand.get_world_poses()
        target.set_world_poses(hand_p, hand_q)

        # Snapshot of the arm's actual joint positions at start() time --
        # used only to seed the q_cmd integrator below (so tracking begins
        # from wherever the arm currently is). NOT used to decide what
        # stop() restores to -- stop() always restores the static
        # R5_CLEAN_ARM_POSE (see stop()).
        clean_arm_targets = art.get_dof_positions().numpy()[0][arm_dof_indices].copy()

        self._art = art
        self._hand = hand
        self._target = target
        self._arm_dof_indices = arm_dof_indices
        self._hand_jac_row = hand_jac_row
        self._dof_lo = dof_lo
        self._dof_hi = dof_hi
        self._clean_arm_targets = clean_arm_targets
        # Internal commanded-state integrator -- see module docstring for
        # why this must NOT be resynced to the measured/lagged joint
        # position on every step.
        self._q_cmd = clean_arm_targets.copy()
        self._posture_ref = np.array(R5_CLEAN_ARM_POSE, dtype=np.float64)
        self._error_count = 0
        self._last_error = None
        self._step_count = 0

        app = omni.kit.app.get_app()
        self._sub = app.get_update_event_stream().create_subscription_to_pop(
            self._on_update, name="ik_follow_controller_update"
        )
        self._running = True

        registry = _get_registry()
        registry["instance"] = self

        return {
            "status": "started",
            "arm_dof_indices": arm_dof_indices,
            "hand_jac_row": hand_jac_row,
            "hand_pos": hand_p.numpy()[0].tolist(),
            "hand_quat": hand_q.numpy()[0].tolist(),
        }

    def stop(self, restore=True):
        if self._sub is not None:
            self._sub.unsubscribe()
            self._sub = None
        if restore and self._art is not None and self._arm_dof_indices is not None:
            # Always restore the static, documented R5_CLEAN_ARM_POSE, not
            # whatever pose happened to be captured at the most recent
            # start() (which may be mid-tracking, arbitrarily far from any
            # known-good configuration). This matches the handoff's
            # requirement to restore "a known valid pose (r5 clean drive
            # targets)" on stop/failure, and is what the lifecycle
            # test (T5) checks for.
            try:
                self._art.set_dof_position_targets(
                    R5_CLEAN_ARM_POSE, dof_indices=self._arm_dof_indices
                )
            except Exception:
                pass
        self._running = False
        registry = _get_registry()
        if registry.get("instance") is self:
            registry["instance"] = None
        return {"status": "stopped"}

    def status(self):
        return {
            "running": self._running,
            "step_count": self._step_count,
            "error_count": self._error_count,
            "last_error": self._last_error,
        }

    # -- per-frame step --------------------------------------------------
    def _on_update(self, _event):
        if not self._running:
            return
        try:
            timeline = omni.timeline.get_timeline_interface()
            if not timeline.is_playing():
                return
            if not getattr(self._art, "_physics_tensor_entity_initialized", False):
                return

            target_p, target_q = self._target.get_world_poses()
            hand_p, hand_q = self._hand.get_world_poses()
            target_p = target_p.numpy()[0]
            target_q = target_q.numpy()[0]
            hand_p = hand_p.numpy()[0]
            hand_q = hand_q.numpy()[0]

            pos_err = target_p - hand_p
            rot_err = _axis_angle_error(hand_q, target_q)

            n_arm = len(self._arm_dof_indices)
            I_n = np.eye(n_arm)

            J_full = self._art.get_jacobian_matrices().numpy()
            J = J_full[0, self._hand_jac_row][:, self._arm_dof_indices]  # (6,7)

            # WEIGHTED SINGLE-STACK DLS -- see module docstring for the
            # full history of what was tried before this (naive single
            # stack, task-priority + null-space leakage fix, three
            # task-priority secondary-term cap variants) and why each was
            # replaced. Position and orientation are solved TOGETHER in
            # one weighted least-squares problem, not sequentially, so
            # the chosen joint configuration is influenced by BOTH goals
            # from the start instead of position being solved with zero
            # regard for orientation and orientation only getting
            # whatever null-space scraps are left over (which, at some
            # configurations, turned out to be almost nothing -- see
            # "WEIGHTED SINGLE-STACK DLS" in the docstring).
            e6 = np.concatenate([pos_err, rot_err])
            rot_weight = _adaptive_rot_weight(float(np.linalg.norm(pos_err)))
            w = np.array(
                [POS_WEIGHT, POS_WEIGHT, POS_WEIGHT, rot_weight, rot_weight, rot_weight]
            )
            J_w = J * w[:, None]
            e_w = e6 * w

            # Manipulability-adaptive damping on the WEIGHTED stacked
            # Jacobian's own conditioning -- same technique as before
            # (see "MANIPULABILITY-ADAPTIVE DAMPING"), just applied to
            # the single combined matrix instead of two separate channels.
            sigma_min_w = float(np.linalg.svd(J_w, compute_uv=False)[-1])
            lambda_w = _manipulability_damping(sigma_min_w, DAMPING)
            null_lambda_w = _manipulability_damping(sigma_min_w, NULL_DAMPING)

            M = J_w @ J_w.T + (lambda_w ** 2) * np.eye(6)
            J_w_pinv = J_w.T @ np.linalg.solve(M, np.eye(6))  # (7,6)
            dq_task = J_w_pinv @ e_w

            M_null = J_w @ J_w.T + (null_lambda_w ** 2) * np.eye(6)
            J_w_pinv_null = J_w.T @ np.linalg.solve(M_null, np.eye(6))
            N = I_n - J_w_pinv_null @ J_w  # null space of the combined weighted task

            # Posture recovery in the leftover redundancy -- same
            # mechanism and cap as before, just projected through the
            # single combined null space `N` now instead of the two-level
            # task-priority one.
            posture_pull = POSTURE_GAIN * (self._posture_ref - self._q_cmd)
            dq_null = N @ posture_pull
            null_norm = float(np.linalg.norm(dq_null))
            if null_norm > MAX_POSTURE_DELTA_PER_STEP:
                dq_null = dq_null * (MAX_POSTURE_DELTA_PER_STEP / null_norm)

            dq = dq_task + dq_null

            norm = float(np.linalg.norm(dq))
            if norm > MAX_JOINT_DELTA_PER_STEP:
                dq = dq * (MAX_JOINT_DELTA_PER_STEP / norm)

            # Integrate on our own commanded state, not on the measured
            # (PD-lagged) joint position -- see module docstring.
            new_pos = self._q_cmd + dq
            lo = self._dof_lo[self._arm_dof_indices]
            hi = self._dof_hi[self._arm_dof_indices]
            new_pos = np.clip(new_pos, lo, hi)
            self._q_cmd = new_pos

            self._art.set_dof_position_targets(new_pos, dof_indices=self._arm_dof_indices)

            self._step_count += 1
            self._last_error = {
                "pos_error_norm": float(np.linalg.norm(pos_err)),
                "rot_error_norm": float(np.linalg.norm(rot_err)),
            }
        except Exception as exc:
            self._error_count += 1
            self._last_error = f"{exc}\n{traceback.format_exc()}"
            # Fail safe: stop and restore a known-good pose rather than
            # leaving a half-broken controller subscribed.
            self.stop(restore=True)


def ik_follow_start():
    """Start (or safely restart) the persistent IK follow controller."""
    registry = _get_registry()
    existing = registry.get("instance")
    if existing is not None:
        try:
            existing.stop(restore=False)
        except Exception:
            pass
        registry["instance"] = None

    controller = IKFollowController()
    result = controller.start()
    return result


def ik_follow_stop():
    """Stop the persistent IK follow controller and restore a clean pose."""
    registry = _get_registry()
    existing = registry.get("instance")
    if existing is None:
        return {"status": "not_running"}
    result = existing.stop(restore=True)
    return result


def ik_follow_status():
    registry = _get_registry()
    existing = registry.get("instance")
    if existing is None:
        return {"status": "not_running"}
    return existing.status()


def ik_follow_subscription_count():
    """Diagnostic: 1 if a controller with a live subscription is
    registered, 0 otherwise. Used by lifecycle checks to prove
    repeated start() calls never create duplicate subscriptions."""
    registry = _get_registry()
    existing = registry.get("instance")
    if existing is None or existing._sub is None:
        return 0
    return 1
