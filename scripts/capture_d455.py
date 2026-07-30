"""GUI-friendly Intel RealSense D455 snapshot capture for the demo scene.

Public entry points:

    demo_capture()                    # recommended: automatic unique run ID
    demo_capture("optional_note")     # optional human-readable suffix
    demo_measure_capture()            # rebuild the unified surface report
    demo_capture_status()             # last capture summary

Each call creates a date-and-sequence folder such as ``2026-0728-1`` under
``outputs/captures`` and writes color,
left/right stereo, raw depth, a region-label image, one complete measurement
report, and one compact human summary. The active stage supplies project
location and provenance; no user home path or scene revision is hardcoded.
"""

import builtins
import datetime as _datetime
import hashlib
import json
import os
import re

import numpy as np


CAMERA_PATHS = {
    "left": (
        "/World/ridgeback_franka/panda_hand/d455_camera/RSD455/"
        "Camera_OmniVision_OV9782_Left"
    ),
    "right": (
        "/World/ridgeback_franka/panda_hand/d455_camera/RSD455/"
        "Camera_OmniVision_OV9782_Right"
    ),
    "color": (
        "/World/ridgeback_franka/panda_hand/d455_camera/RSD455/"
        "Camera_OmniVision_OV9782_Color"
    ),
}
IK_TARGET_PATH = "/World/IKTarget"
HAND_PATH = "/World/ridgeback_franka/panda_hand"
WIDTH = 640
HEIGHT = 480
# RTX's aspect-ratio fit makes the effective focal length differ from the
# naive USD aperture calculation at 640x480. Empirical RTX calibration measured
# and independently validated this square-pixel value to below 1% error.
FOCAL_LENGTH_PX = 307.7776730991483
PRINCIPAL_POINT_PX = (WIDTH / 2.0, HEIGHT / 2.0)
BORDER_MARGIN_PX = 2
REGISTRY_NAME = "_d455_demo_capture_registry"


def _registry():
    if not hasattr(builtins, REGISTRY_NAME):
        setattr(
            builtins,
            REGISTRY_NAME,
            {
                "stage_id": None,
                "render_products": None,
                "annotators": None,
                "last_summary": None,
            },
        )
    return getattr(builtins, REGISTRY_NAME)


def _active_stage_context():
    import omni.usd

    context = omni.usd.get_context()
    stage = context.get_stage()
    if stage is None:
        raise RuntimeError("No USD stage is open.")
    layer = stage.GetRootLayer()
    stage_path = layer.realPath or layer.identifier
    if not stage_path or not os.path.isfile(stage_path):
        raise RuntimeError(
            "The active stage must be a saved local USD before demo capture."
        )
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(stage_path)))
    output_root = os.environ.get(
        "D455_DEMO_OUTPUT_DIR", os.path.join(project_root, "outputs", "captures")
    )
    return context, stage, os.path.abspath(stage_path), os.path.abspath(output_root)


def _sanitize_label(label):
    if label is None:
        return None
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", str(label).strip()).strip("-._")
    return value[:48] or None


def _create_unique_run_dir(output_root, label=None):
    os.makedirs(output_root, exist_ok=True)
    now_utc = _datetime.datetime.now(_datetime.timezone.utc)
    timestamp = now_utc.strftime("%Y%m%dT%H%M%S%fZ")
    date_prefix = now_utc.astimezone().strftime("%Y-%m%d")
    suffix = _sanitize_label(label)
    existing_pattern = re.compile(
        rf"^{re.escape(date_prefix)}-(\d+)(?:-[A-Za-z0-9._-]+)?$"
    )
    existing_numbers = []
    for name in os.listdir(output_root):
        match = existing_pattern.match(name)
        if match and os.path.isdir(os.path.join(output_root, name)):
            existing_numbers.append(int(match.group(1)))
    first_sequence = max(existing_numbers, default=0) + 1
    for sequence in range(first_sequence, first_sequence + 1000):
        base = f"{date_prefix}-{sequence}"
        run_id = base if suffix is None else f"{base}-{suffix}"
        run_dir = os.path.join(output_root, run_id)
        try:
            os.makedirs(run_dir)
            return run_id, run_dir, timestamp, suffix, sequence
        except FileExistsError:
            continue
    raise RuntimeError("Could not allocate a unique capture directory.")


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _camera_frame(stage, camera_path):
    import omni.timeline

    prim = stage.GetPrimAtPath(camera_path)
    if not prim.IsValid():
        raise RuntimeError(f"Camera prim not found: {camera_path}")
    if omni.timeline.get_timeline_interface().is_playing():
        from isaacsim.core.experimental.prims import XformPrim

        positions, quaternions = XformPrim(camera_path).get_world_poses()
        position = positions.numpy()[0].astype(np.float64)
        w, x, y, z = quaternions.numpy()[0].astype(np.float64)
        rotation = np.array(
            [
                [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
            ],
            dtype=np.float64,
        )
        right, up, back = rotation[:, 0], rotation[:, 1], rotation[:, 2]
    else:
        from pxr import Usd, UsdGeom

        matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(
            Usd.TimeCode.Default()
        )
        position = np.asarray(matrix.ExtractTranslation(), dtype=np.float64)
        authored_rotation = matrix.ExtractRotationMatrix()
        axes = np.array(
            [
                [authored_rotation[row][column] for column in range(3)]
                for row in range(3)
            ],
            dtype=np.float64,
        )
        right, up, back = axes[0], axes[1], axes[2]
    right = right / np.linalg.norm(right)
    up = up / np.linalg.norm(up)
    forward = -back / np.linalg.norm(back)
    return {
        "position_m": position.tolist(),
        "right": right.tolist(),
        "up": up.tolist(),
        "forward": forward.tolist(),
    }


def _force_render_step(rt_subframes=4):
    try:
        import omni.replicator.core as rep

        rep.orchestrator.step(
            rt_subframes=rt_subframes,
            pause_timeline=False,
            wait_for_render=True,
        )
        return "replicator_orchestrator"
    except Exception:
        import omni.kit.app

        app = omni.kit.app.get_app()
        for _ in range(max(1, rt_subframes)):
            app.update()
        return "app_update_fallback"


def _read_rgb_with_retry(annotator, max_retries=4, minimum_mean=1.0):
    attempts = []
    image = None
    for attempt in range(max_retries + 1):
        image = np.asarray(annotator.get_data())[:, :, :3].astype(np.uint8)
        mean = float(image.mean())
        attempts.append(mean)
        if mean >= minimum_mean:
            return image, {
                "mean_at_each_attempt": attempts,
                "retries": attempt,
                "valid": True,
            }
        _force_render_step()
    return image, {
        "mean_at_each_attempt": attempts,
        "retries": max_retries,
        "valid": False,
    }


def _wait_for_ik_settle(max_frames=180, stable_frames=5):
    """Wait for the running demo IK controller to reach its target.

    If no controller is active, only a short render warm-up is performed. The
    operator can therefore capture a static scene without enabling IK.
    """
    import omni.kit.app

    app = omni.kit.app.get_app()
    controller_registry = getattr(
        builtins, "_ik_follow_controller_registry", {"instance": None}
    )
    controller = controller_registry.get("instance")
    if controller is None:
        for _ in range(10):
            app.update()
        return {"settled": True, "reason": "IK controller is not running"}

    stable = 0
    last_status = None
    for frame in range(1, max_frames + 1):
        app.update()
        last_status = controller.status()
        error = last_status.get("last_error")
        if isinstance(error, dict):
            position_ok = error.get("pos_error_norm", 999.0) <= 0.003
            orientation_ok = error.get("rot_error_norm", 999.0) <= 0.05
            stable = stable + 1 if position_ok and orientation_ok else 0
            if stable >= stable_frames:
                return {
                    "settled": True,
                    "frames": frame,
                    "controller_status": last_status,
                }
    return {
        "settled": False,
        "frames": max_frames,
        "controller_status": last_status,
        "reason": "IK target did not converge before capture timeout",
    }


def demo_capture_setup(force=False):
    """Create and cache the three camera render products for the active stage."""
    import omni.kit.app
    import omni.replicator.core as rep
    import omni.timeline

    context, stage, _, _ = _active_stage_context()
    registry = _registry()
    stage_id = context.get_stage_id()
    if (
        not force
        and registry["stage_id"] == stage_id
        and registry["render_products"] is not None
    ):
        return {"status": "already_setup", "stage_id": stage_id}

    render_products = {}
    annotators = {}
    for eye, path in CAMERA_PATHS.items():
        if not stage.GetPrimAtPath(path).IsValid():
            raise RuntimeError(f"Camera prim not found: {path}")
        product = rep.create.render_product(path, (WIDTH, HEIGHT))
        render_products[eye] = product
        eye_annotators = {"rgb": rep.AnnotatorRegistry.get_annotator("rgb")}
        eye_annotators["rgb"].attach(product)
        if eye in ("left", "right"):
            for name in ("distance_to_image_plane", "distance_to_camera"):
                eye_annotators[name] = rep.AnnotatorRegistry.get_annotator(name)
                eye_annotators[name].attach(product)
        annotators[eye] = eye_annotators

    timeline = omni.timeline.get_timeline_interface()
    was_playing = timeline.is_playing()
    if not was_playing:
        timeline.play()
    app = omni.kit.app.get_app()
    for _ in range(30):
        app.update()
    render_method = _force_render_step(rt_subframes=8)

    registry.update(
        {
            "stage_id": stage_id,
            "render_products": render_products,
            "annotators": annotators,
            "last_summary": None,
        }
    )
    return {
        "status": "setup_complete",
        "stage_id": stage_id,
        "timeline_was_playing": was_playing,
        "render_method": render_method,
    }


def _save_png(array, path):
    from PIL import Image

    Image.fromarray(array.astype(np.uint8)).save(path)


def _depth_preview(depth):
    valid_mask = np.isfinite(depth) & (depth > 0)
    preview = np.zeros(depth.shape, dtype=np.uint8)
    if np.any(valid_mask):
        values = depth[valid_mask]
        low, high = np.percentile(values, [2.0, 98.0])
        scaled = np.clip((depth - low) / max(float(high - low), 1e-6), 0.0, 1.0)
        preview[valid_mask] = (scaled[valid_mask] * 255.0).astype(np.uint8)
    return np.stack([preview, preview, preview], axis=-1)


def _annotation_font(size=16):
    from PIL import ImageFont

    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _draw_marker(
    draw,
    point,
    label,
    color,
    image_size,
    occupied_boxes=None,
    include_coordinates=True,
):
    """Draw a high-contrast crosshair and its image-pixel coordinate."""
    u, v = (int(round(value)) for value in point)
    width, height = image_size
    radius = 10
    outline = (0, 0, 0, 255)
    fill = tuple(color) + (255,)
    for line_width, line_color in ((7, outline), (3, fill)):
        draw.line((u - radius, v, u + radius, v), fill=line_color, width=line_width)
        draw.line((u, v - radius, u, v + radius), fill=line_color, width=line_width)
    draw.ellipse(
        (u - 4, v - 4, u + 4, v + 4),
        fill=fill,
        outline=outline,
        width=2,
    )
    if label is None:
        return None
    text = f"{label} ({u},{v})" if include_coordinates else label
    font = _annotation_font()
    text_box = draw.textbbox((0, 0), text, font=font, stroke_width=1)
    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]
    candidates = (
        (u + 13, v - text_height - 12),
        (u - text_width - 13, v - text_height - 12),
        (u + 13, v + 10),
        (u - text_width - 13, v + 10),
    )
    occupied_boxes = occupied_boxes if occupied_boxes is not None else []
    best = None
    for candidate_x, candidate_y in candidates:
        text_x = min(max(2, candidate_x), max(2, width - text_width - 8))
        text_y = min(max(2, candidate_y), max(2, height - text_height - 8))
        box = (
            text_x - 4,
            text_y - 3,
            text_x + text_width + 4,
            text_y + text_height + 3,
        )
        overlap = sum(
            max(0, min(box[2], other[2]) - max(box[0], other[0]))
            * max(0, min(box[3], other[3]) - max(box[1], other[1]))
            for other in occupied_boxes
        )
        if best is None or overlap < best[0]:
            best = (overlap, text_x, text_y, box)
        if overlap == 0:
            break
    _, text_x, text_y, label_box = best
    draw.rounded_rectangle(
        (text_x - 4, text_y - 3, text_x + text_width + 4, text_y + text_height + 3),
        radius=3,
        fill=(0, 0, 0, 210),
        outline=fill,
        width=2,
    )
    draw.text(
        (text_x, text_y),
        text,
        font=font,
        fill=(255, 255, 255, 255),
        stroke_width=1,
        stroke_fill=(0, 0, 0, 255),
    )
    occupied_boxes.append(label_box)
    return label_box


def _write_visual_validation(capture_directory, target_records, label_image):
    """Write marker and mask overlays for reported targets only."""
    from PIL import Image, ImageDraw

    palette = (
        (255, 45, 45),
        (0, 220, 255),
        (255, 214, 0),
        (255, 70, 220),
        (80, 255, 80),
        (255, 140, 0),
        (130, 100, 255),
        (255, 255, 255),
    )
    target_annotations = [
        {
            "target_rank": target_rank,
            "surface_id": record["region_id"],
            "representative_pixel_px": record["representative_point"]["pixel_px"],
            "representative_axial_depth_m": record["distance_m"][
                "representative_axial_z_forward"
            ],
            "rgb_marker_label": f"T{target_rank}",
            "depth_marker_label": (
                f"T{target_rank} "
                f"{record['distance_m']['representative_axial_z_forward']:.3f} m"
            ),
        }
        for target_rank, record in enumerate(target_records, start=1)
    ]

    for source_name, output_name, label_field, include_coordinates in (
        (
            "rgb_left.png",
            "rgb_left_annotated.png",
            "rgb_marker_label",
            True,
        ),
        (
            "depth_preview.png",
            "depth_preview_annotated.png",
            "depth_marker_label",
            False,
        ),
    ):
        image = Image.open(os.path.join(capture_directory, source_name)).convert("RGBA")
        draw = ImageDraw.Draw(image, "RGBA")
        occupied_boxes = []
        for annotation in target_annotations:
            color = palette[(annotation["target_rank"] - 1) % len(palette)]
            _draw_marker(
                draw,
                annotation["representative_pixel_px"],
                annotation[label_field],
                color,
                image.size,
                occupied_boxes=occupied_boxes,
                include_coordinates=include_coordinates,
            )
        image.convert("RGB").save(os.path.join(capture_directory, output_name))

    rgb = np.asarray(
        Image.open(os.path.join(capture_directory, "rgb_left.png")).convert("RGB"),
        dtype=np.uint8,
    )
    overlay = rgb.astype(np.float32)
    for record in target_records:
        label_value = record["visibility"]["region_mask"]["label_value"]
        target_rank = record["target_rank"]
        color = np.asarray(
            palette[(target_rank - 1) % len(palette)], dtype=np.float32
        )
        mask = label_image == label_value
        overlay[mask] = 0.58 * overlay[mask] + 0.42 * color
    overlay_image = Image.fromarray(
        np.clip(overlay, 0, 255).astype(np.uint8), mode="RGB"
    ).convert("RGBA")
    draw = ImageDraw.Draw(overlay_image, "RGBA")
    font = _annotation_font(14)
    for record in target_records:
        label_value = record["visibility"]["region_mask"]["label_value"]
        target_rank = record["target_rank"]
        color = palette[(target_rank - 1) % len(palette)]
        left, top, right, bottom = record["visibility"]["bbox_px"]
        draw.rectangle(
            (left, top, right, bottom),
            outline=tuple(color) + (255,),
            width=2,
        )
        centroid_u, centroid_v = record["visibility"]["centroid_px"]
        draw.ellipse(
            (
                centroid_u - 3,
                centroid_v - 3,
                centroid_u + 3,
                centroid_v + 3,
            ),
            fill=(255, 255, 255, 255),
            outline=(0, 0, 0, 255),
            width=1,
        )
        _draw_marker(
            draw,
            record["representative_point"]["pixel_px"],
            None,
            color,
            overlay_image.size,
        )
        short_hint = (
            "wall" if record["semantic_hint"] == "likely_wall" else "target"
        )
        draw.text(
            (left + 3, min(bottom - 16, top + 3)),
            f"T{target_rank} {short_hint}",
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255),
        )
    overlay_image.convert("RGB").save(
        os.path.join(capture_directory, "region_overlay.png")
    )
    return target_annotations


def _usd_validation_candidates(stage):
    """Return optional oracle labels used only after image measurement."""
    from pxr import Usd, UsdGeom

    candidates = []
    for prim in stage.Traverse():
        if not (prim.IsA(UsdGeom.Cube) or prim.IsA(UsdGeom.Sphere)):
            continue
        path = str(prim.GetPath())
        if (
            path.startswith("/World/ridgeback_franka/")
            or path.startswith("/World/GroundPlane/")
            or path == IK_TARGET_PATH
        ):
            continue
        phase_color = prim.GetAttribute("phase5:color_name")
        color_name = (
            phase_color.Get()
            if phase_color.IsValid() and phase_color.Get()
            else None
        )
        phase_shape = prim.GetAttribute("phase5:shape")
        shape = (
            phase_shape.Get()
            if phase_shape.IsValid() and phase_shape.Get()
            else prim.GetTypeName().lower()
        )
        matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(
            Usd.TimeCode.Default()
        )
        candidates.append(
            {
                "prim_path": path,
                "color_name": color_name,
                "shape": shape,
                "authored_center_world_xyz_m": np.asarray(
                    matrix.ExtractTranslation(), dtype=np.float64
                ),
            }
        )
    return candidates


def _connected_depth_regions(
    axial_depth,
    minimum_depth_m=0.05,
    maximum_depth_m=5.0,
    minimum_pixels=64,
    discontinuity_absolute_m=0.02,
    discontinuity_relative=0.025,
    border_margin_px=BORDER_MARGIN_PX,
):
    """Region-grow valid depth pixels until a physical depth discontinuity.

    The operation uses no RGB information. It finds continuous visible
    surfaces, not semantic object instances; two touching surfaces with no
    measurable depth break may therefore remain one region.
    """
    valid = (
        np.isfinite(axial_depth)
        & (axial_depth >= minimum_depth_m)
        & (axial_depth <= maximum_depth_m)
    )
    height, width = axial_depth.shape
    visited = np.zeros(valid.shape, dtype=bool)
    regions = []
    for start_v in range(height):
        for start_u in range(width):
            if not valid[start_v, start_u] or visited[start_v, start_u]:
                continue
            stack = [(start_v, start_u)]
            visited[start_v, start_u] = True
            rows = []
            columns = []
            while stack:
                v, u = stack.pop()
                rows.append(v)
                columns.append(u)
                current_depth = float(axial_depth[v, u])
                for neighbor_v, neighbor_u in (
                    (v - 1, u),
                    (v + 1, u),
                    (v, u - 1),
                    (v, u + 1),
                ):
                    if not (
                        0 <= neighbor_v < height
                        and 0 <= neighbor_u < width
                        and valid[neighbor_v, neighbor_u]
                        and not visited[neighbor_v, neighbor_u]
                    ):
                        continue
                    neighbor_depth = float(
                        axial_depth[neighbor_v, neighbor_u]
                    )
                    tolerance = max(
                        discontinuity_absolute_m,
                        discontinuity_relative
                        * min(current_depth, neighbor_depth),
                    )
                    if abs(neighbor_depth - current_depth) <= tolerance:
                        visited[neighbor_v, neighbor_u] = True
                        stack.append((neighbor_v, neighbor_u))
            if len(rows) < minimum_pixels:
                continue
            rows = np.asarray(rows, dtype=np.int32)
            columns = np.asarray(columns, dtype=np.int32)
            minimum_u = int(columns.min())
            maximum_u = int(columns.max())
            minimum_v = int(rows.min())
            maximum_v = int(rows.max())
            touches_border = bool(
                minimum_u <= border_margin_px
                or minimum_v <= border_margin_px
                or maximum_u >= width - 1 - border_margin_px
                or maximum_v >= height - 1 - border_margin_px
            )
            regions.append(
                {
                    "rows": rows,
                    "columns": columns,
                    "pixel_count": int(len(rows)),
                    "bbox_px": [minimum_u, minimum_v, maximum_u, maximum_v],
                    "centroid_px": [
                        float(columns.mean()),
                        float(rows.mean()),
                    ],
                    "touches_image_border": touches_border,
                    "image_border_margin_px": border_margin_px,
                    "image_fraction": float(len(rows) / (height * width)),
                }
            )
    return regions


def _depth_world_normal_map(
    axial_depth,
    right,
    up,
    forward,
    minimum_depth_m,
    maximum_depth_m,
    discontinuity_absolute_m,
    discontinuity_relative,
):
    """Estimate per-pixel visible-surface normals in world coordinates."""
    height, width = axial_depth.shape
    columns, rows = np.meshgrid(np.arange(width), np.arange(height))
    cx, cy = PRINCIPAL_POINT_PX
    valid = (
        np.isfinite(axial_depth)
        & (axial_depth >= minimum_depth_m)
        & (axial_depth <= maximum_depth_m)
    )
    camera_points = np.full((height, width, 3), np.nan, dtype=np.float64)
    with np.errstate(invalid="ignore"):
        camera_points[:, :, 0] = (
            (columns - cx) / FOCAL_LENGTH_PX * axial_depth
        )
        camera_points[:, :, 1] = (
            -(rows - cy) / FOCAL_LENGTH_PX * axial_depth
        )
        camera_points[:, :, 2] = axial_depth
        horizontal = (
            camera_points[1:-1, 2:] - camera_points[1:-1, :-2]
        )
        vertical = camera_points[2:, 1:-1] - camera_points[:-2, 1:-1]
        normal_camera = np.cross(horizontal, vertical)
    lengths = np.linalg.norm(normal_camera, axis=2)
    normal_valid = np.isfinite(lengths) & (lengths > 1e-9)
    normal_camera[normal_valid] /= lengths[normal_valid, None]

    normal_world = np.full((height, width, 3), np.nan, dtype=np.float64)
    interior_world = (
        normal_camera[:, :, 0, None] * right
        + normal_camera[:, :, 1, None] * up
        + normal_camera[:, :, 2, None] * forward
    )
    normal_world[1:-1, 1:-1] = interior_world

    center = axial_depth[1:-1, 1:-1]
    continuous = valid[1:-1, 1:-1].copy()
    for neighbor in (
        axial_depth[1:-1, :-2],
        axial_depth[1:-1, 2:],
        axial_depth[:-2, 1:-1],
        axial_depth[2:, 1:-1],
    ):
        with np.errstate(invalid="ignore"):
            tolerance = np.maximum(
                discontinuity_absolute_m,
                discontinuity_relative * np.minimum(center, neighbor),
            )
            continuous &= (
                np.isfinite(neighbor)
                & (np.abs(neighbor - center) <= tolerance)
            )
    reliable = np.zeros(valid.shape, dtype=bool)
    reliable[1:-1, 1:-1] = continuous & normal_valid
    return normal_world, reliable


def _split_large_region_into_planes(
    region,
    axial_depth,
    normal_world,
    reliable_normals,
    minimum_depth_m,
    maximum_depth_m,
    minimum_pixels,
    discontinuity_absolute_m,
    discontinuity_relative,
):
    """Split a large merged surface into horizontal/vertical plane candidates."""
    region_mask = np.zeros(axial_depth.shape, dtype=bool)
    region_mask[region["rows"], region["columns"]] = True
    absolute_world_z = np.abs(normal_world[:, :, 2])
    categories = (
        (
            "horizontal_plane_candidate",
            "likely_floor",
            reliable_normals & (absolute_world_z >= 0.85),
        ),
        (
            "vertical_plane_candidate",
            "likely_wall",
            reliable_normals & (absolute_world_z <= 0.25),
        ),
    )
    plane_minimum_pixels = max(500, minimum_pixels)
    splits = []
    for orientation_hint, semantic_hint, category_mask in categories:
        masked_depth = np.where(
            region_mask & category_mask, axial_depth, np.inf
        ).astype(np.float32)
        components = _connected_depth_regions(
            masked_depth,
            minimum_depth_m=minimum_depth_m,
            maximum_depth_m=maximum_depth_m,
            minimum_pixels=plane_minimum_pixels,
            discontinuity_absolute_m=discontinuity_absolute_m,
            discontinuity_relative=discontinuity_relative,
        )
        for component in components:
            component["surface_kind"] = "plane"
            component["orientation_hint"] = orientation_hint
            component["semantic_hint"] = semantic_hint
            splits.append(component)
    covered_pixels = sum(item["pixel_count"] for item in splits)
    if covered_pixels < 0.5 * region["pixel_count"]:
        return []
    return splits


def _attach_post_measurement_gui_labels(region_records, stage):
    """Attach optional USD names after sensor-only detection for GUI review."""
    if stage is None:
        return
    candidates = _usd_validation_candidates(stage)
    available = set(range(len(candidates)))
    for record in region_records:
        if record["semantic_hint"] == "likely_floor" or not available:
            continue
        point = np.asarray(
            record["coordinates_m"]["surface_world_xyz"], dtype=np.float64
        )
        ranked = sorted(
            (
                float(
                    np.linalg.norm(
                        point
                        - candidates[index]["authored_center_world_xyz_m"]
                    )
                ),
                index,
            )
            for index in available
        )
        distance, index = ranked[0]
        if distance > 0.75:
            continue
        candidate = candidates[index]
        available.remove(index)
        record["gui_validation_label"] = {
            "source": "post_measurement_usd_nearest_center",
            "used_for_depth_detection": False,
            "prim_path": candidate["prim_path"],
            "shape": candidate["shape"],
            "authored_center_world_xyz_m": candidate[
                "authored_center_world_xyz_m"
            ].tolist(),
            "surface_point_to_authored_center_m": distance,
        }


def demo_measure_capture(
    capture_directory=None,
    stage=None,
    minimum_depth_m=0.05,
    maximum_depth_m=5.0,
    minimum_pixels=64,
    discontinuity_absolute_m=0.02,
    discontinuity_relative=0.025,
):
    """Measure depth-continuous visible surfaces and order them near to far."""
    if capture_directory is None:
        latest = _registry().get("last_summary")
        if not latest:
            raise RuntimeError("No capture is available; call demo_capture() first.")
        capture_directory = latest["output_directory"]
    capture_directory = os.path.abspath(capture_directory)
    with open(
        os.path.join(capture_directory, "capture.json"),
        "r",
        encoding="utf-8",
    ) as source:
        capture_metadata = json.load(source)
    if stage is None:
        try:
            import omni.usd

            stage = omni.usd.get_context().get_stage()
        except ImportError:
            stage = None
    axial = np.load(os.path.join(capture_directory, "depth_axial_left.npy"))

    frame = capture_metadata["camera_frames"]["left"]
    camera_position = np.asarray(frame["position_m"], dtype=np.float64)
    right = np.asarray(frame["right"], dtype=np.float64)
    up = np.asarray(frame["up"], dtype=np.float64)
    forward = np.asarray(frame["forward"], dtype=np.float64)
    cx, cy = PRINCIPAL_POINT_PX
    region_records = []
    pixel_membership = {}
    regions = _connected_depth_regions(
        axial,
        minimum_depth_m=minimum_depth_m,
        maximum_depth_m=maximum_depth_m,
        minimum_pixels=minimum_pixels,
        discontinuity_absolute_m=discontinuity_absolute_m,
        discontinuity_relative=discontinuity_relative,
    )
    normal_world, reliable_normals = _depth_world_normal_map(
        axial,
        right,
        up,
        forward,
        minimum_depth_m,
        maximum_depth_m,
        discontinuity_absolute_m,
        discontinuity_relative,
    )
    expanded_regions = []
    for region in regions:
        is_large_border_surface = (
            region["touches_image_border"]
            and region["image_fraction"] >= 0.25
        )
        splits = []
        if is_large_border_surface:
            splits = _split_large_region_into_planes(
                region,
                axial,
                normal_world,
                reliable_normals,
                minimum_depth_m,
                maximum_depth_m,
                minimum_pixels,
                discontinuity_absolute_m,
                discontinuity_relative,
            )
        if splits:
            expanded_regions.extend(splits)
        else:
            region["surface_kind"] = "depth_region"
            region["orientation_hint"] = None
            region["semantic_hint"] = "object_candidate"
            expanded_regions.append(region)
    regions = expanded_regions

    for region in regions:
        surface_kind = region.pop("surface_kind")
        orientation_hint = region.pop("orientation_hint")
        semantic_hint = region.pop("semantic_hint")
        rows = region.pop("rows")
        columns = region.pop("columns")
        axial_values = axial[rows, columns].astype(np.float64)
        centroid_u, centroid_v = region["centroid_px"]
        spatial_distance = (columns - centroid_u) ** 2 + (rows - centroid_v) ** 2
        representative = int(np.argmin(spatial_distance))
        u = float(columns[representative])
        v = float(rows[representative])
        depth = float(axial[rows[representative], columns[representative]])
        x_right = (u - cx) / FOCAL_LENGTH_PX * depth
        y_up = -(v - cy) / FOCAL_LENGTH_PX * depth
        camera_xyz = np.asarray([x_right, y_up, depth], dtype=np.float64)
        world_xyz = (
            camera_position + x_right * right + y_up * up + depth * forward
        )
        all_x_right = (columns - cx) / FOCAL_LENGTH_PX * axial_values
        all_y_up = -(rows - cy) / FOCAL_LENGTH_PX * axial_values
        camera_points = np.column_stack(
            (all_x_right, all_y_up, axial_values)
        )
        camera_ranges = np.linalg.norm(camera_points, axis=1)
        world_points = (
            camera_position
            + all_x_right[:, None] * right
            + all_y_up[:, None] * up
            + axial_values[:, None] * forward
        )
        if surface_kind == "plane":
            role_hint = orientation_hint
        else:
            role_hint = (
                "large_border_surface"
                if region["touches_image_border"]
                and region["image_fraction"] >= 0.25
                else "bounded_surface_candidate"
            )
        measured_surface_z_m = float(np.median(world_points[:, 2]))
        is_environment_floor = (
            semantic_hint == "likely_floor"
            and abs(measured_surface_z_m) <= 0.15
        )
        if is_environment_floor:
            classification = {
                "reporting_category": "environment_surface",
                "basis": (
                    "large horizontal world-space surface with measured "
                    "median Z within 0.15 m of the world origin"
                ),
                "measured_median_world_z_m": measured_surface_z_m,
            }
        elif semantic_hint == "likely_wall":
            classification = {
                "reporting_category": "reported_target",
                "basis": "vertical world-space surface normal",
            }
        else:
            classification = {
                "reporting_category": "reported_target",
                "basis": (
                    "depth-connected visible surface not meeting the "
                    "environment-floor exclusion rule"
                ),
            }
        axial_percentiles = np.percentile(
            axial_values, [0.0, 2.0, 50.0, 98.0, 100.0]
        )
        range_percentiles = np.percentile(
            camera_ranges, [0.0, 2.0, 50.0, 98.0, 100.0]
        )
        record = {
            "surface_kind": surface_kind,
            "role_hint": role_hint,
            "semantic_hint": semantic_hint,
            "classification": classification,
            "representative_point": {
                "definition": (
                    "Valid region pixel nearest the 2D mask centroid; "
                    "this is a visible surface point, not the object center."
                ),
                "pixel_px": [u, v],
            },
            "visibility": {
                **region,
                "representative_pixel_px": [u, v],
            },
            "coordinates_m": {
                "surface_camera_xyz": {
                    "x_right": float(camera_xyz[0]),
                    "y_up": float(camera_xyz[1]),
                    "z_forward": float(camera_xyz[2]),
                },
                "surface_world_xyz": world_xyz.tolist(),
            },
            "distance_m": {
                "camera_to_representative_surface": float(
                    np.linalg.norm(camera_xyz)
                ),
                "representative_axial_z_forward": depth,
                "surface_to_world_origin": float(np.linalg.norm(world_xyz)),
            },
            "visible_surface_extent_m": {
                "camera_axis_aligned": {
                    "minimum_xyz": np.min(camera_points, axis=0).tolist(),
                    "maximum_xyz": np.max(camera_points, axis=0).tolist(),
                },
                "world_axis_aligned": {
                    "minimum_xyz": np.min(world_points, axis=0).tolist(),
                    "maximum_xyz": np.max(world_points, axis=0).tolist(),
                },
            },
            "surface_depth_profile_m": {
                "axial_z_forward": {
                    "minimum": float(axial_percentiles[0]),
                    "p02": float(axial_percentiles[1]),
                    "median": float(axial_percentiles[2]),
                    "p98": float(axial_percentiles[3]),
                    "maximum": float(axial_percentiles[4]),
                },
                "euclidean_camera_range": {
                    "minimum": float(range_percentiles[0]),
                    "p02": float(range_percentiles[1]),
                    "median": float(range_percentiles[2]),
                    "p98": float(range_percentiles[3]),
                    "maximum": float(range_percentiles[4]),
                },
                "robust_axial_span_p02_to_p98": float(
                    axial_percentiles[3] - axial_percentiles[1]
                ),
            },
        }
        if surface_kind == "plane":
            component_normals = normal_world[rows, columns]
            finite_normals = np.all(np.isfinite(component_normals), axis=1)
            median_normal = np.median(
                component_normals[finite_normals], axis=0
            )
            median_normal /= np.linalg.norm(median_normal)
            if np.dot(median_normal, camera_position - world_xyz) < 0.0:
                median_normal = -median_normal
            coordinate_medians = np.median(world_points, axis=0)
            coordinate_mad = np.median(
                np.abs(world_points - coordinate_medians), axis=0
            )
            constant_axis_index = int(np.argmin(coordinate_mad))
            axis_names = ("x", "y", "z")
            plane_offset = float(np.dot(median_normal, coordinate_medians))
            plane_record = {
                "normal_world_unit": median_normal.tolist(),
                "point_world_xyz_m": coordinate_medians.tolist(),
                "equation": {
                    "form": "dot(normal_world_unit, world_xyz) = offset_m",
                    "offset_m": plane_offset,
                },
                "camera_perpendicular_distance_m": float(
                    abs(np.dot(median_normal, camera_position) - plane_offset)
                ),
            }
            axis_alignment = float(np.max(np.abs(median_normal)))
            if axis_alignment >= 0.95:
                plane_record["constant_world_axis"] = {
                    "axis": axis_names[constant_axis_index],
                    "surface_value_m": float(
                        coordinate_medians[constant_axis_index]
                    ),
                    "median_absolute_deviation_m": float(
                        coordinate_mad[constant_axis_index]
                    ),
                    "normal_axis_alignment": axis_alignment,
                }
            record["surface_model"] = {
                "kind": "plane",
                **plane_record,
            }
        else:
            record["surface_model"] = {
                "kind": "sampled_visible_surface",
                "exact_samples": {
                    "depth_file": "depth_axial_left.npy",
                    "region_label_file": "depth_region_labels.npy",
                    "region_label_value": None,
                    "reconstruction": (
                        "Select pixels with this label and back-project axial "
                        "depth using the report camera intrinsics and basis."
                    ),
                },
            }
        region_records.append(record)
        pixel_membership[id(record)] = (rows, columns)

    _attach_post_measurement_gui_labels(region_records, stage)
    region_records.sort(
        key=lambda item: item["distance_m"][
            "camera_to_representative_surface"
        ]
    )
    gui_validation_records = []
    for index, record in enumerate(region_records, start=1):
        record["region_id"] = f"depth-region-{index:03d}"
        record["near_to_far_rank"] = index
        gui_label = record.pop("gui_validation_label", None)
        if gui_label is not None:
            gui_validation_records.append(
                {"surface_id": record["region_id"], **gui_label}
            )
        record["visibility"]["region_mask"] = {
            "file": "depth_region_labels.npy",
            "encoding": "uint16 label image aligned to the left camera",
            "label_value": index,
        }
        if record["surface_model"]["kind"] == "sampled_visible_surface":
            record["surface_model"]["exact_samples"][
                "region_label_value"
            ] = index

    target_records = [
        record
        for record in region_records
        if record["classification"]["reporting_category"] == "reported_target"
    ]
    environment_records = [
        record
        for record in region_records
        if record["classification"]["reporting_category"]
        == "environment_surface"
    ]
    for target_rank, record in enumerate(target_records, start=1):
        record["target_rank"] = target_rank

    label_image = np.zeros(axial.shape, dtype=np.uint16)
    for record in region_records:
        rows, columns = pixel_membership[id(record)]
        label_image[rows, columns] = record["near_to_far_rank"]
    np.save(
        os.path.join(capture_directory, "depth_region_labels.npy"), label_image
    )

    measurement = {
        "schema": "d455-reported-targets-v3",
        "status": "pass",
        "capture_id": capture_metadata["run_id"],
        "capture_timestamp_utc": capture_metadata["timestamp_utc"],
        "stage": capture_metadata["stage"],
        "method": {
            "primary_input": "depth_axial_left.npy",
            "region_membership_output": "depth_region_labels.npy",
            "uses_rgb": False,
            "uses_usd_oracle": False,
            "minimum_depth_m": minimum_depth_m,
            "maximum_depth_m": maximum_depth_m,
            "minimum_pixels": minimum_pixels,
            "discontinuity_absolute_m": discontinuity_absolute_m,
            "discontinuity_relative": discontinuity_relative,
            "large_region_plane_split": {
                "horizontal_abs_world_normal_z_minimum": 0.85,
                "vertical_abs_world_normal_z_maximum": 0.25,
                "minimum_plane_pixels": max(500, minimum_pixels),
            },
            "environment_floor_exclusion": {
                "requires_likely_floor_normal_class": True,
                "maximum_absolute_median_world_z_m": 0.15,
                "uses_usd_oracle": False,
            },
            "semantics": (
                "Depth-continuous visible surfaces, not semantic object instances."
            ),
        },
        "camera": {
            "name": "left",
            "world_position_xyz_m": camera_position.tolist(),
            "right_world_unit": right.tolist(),
            "up_world_unit": up.tolist(),
            "forward_world_unit": forward.tolist(),
            "coordinate_convention": {
                "x": "image right",
                "y": "image up",
                "z": "camera forward",
            },
            "intrinsics_px": {
                "fx": FOCAL_LENGTH_PX,
                "fy": FOCAL_LENGTH_PX,
                "cx": cx,
                "cy": cy,
                "source": "empirical RTX 640x480 calibration",
            },
        },
        "sensor_region_count": len(region_records),
        "reported_target_count": len(target_records),
        "excluded_environment_region_count": len(environment_records),
        "reported_targets_near_to_far": target_records,
        "excluded_environment_regions": [
            {
                "region_id": record["region_id"],
                "semantic_hint": record["semantic_hint"],
                "exclusion_reason": (
                    "Known environment floor; retained only in the raw region "
                    "label evidence and excluded from target reporting."
                ),
                "visibility": {
                    "pixel_count": record["visibility"]["pixel_count"],
                    "bbox_px": record["visibility"]["bbox_px"],
                    "region_mask": record["visibility"]["region_mask"],
                },
            }
            for record in environment_records
        ],
        "raw_evidence": {
            "axial_depth": "depth_axial_left.npy",
            "radial_depth": "depth_radial_left.npy",
            "region_labels": "depth_region_labels.npy",
            "left_rgb": "rgb_left.png",
        },
        "oracle_policy": {
            "purpose": "GUI name and authored-center validation only",
            "used_for_detection": False,
            "unseen_stage_objects_are_recorded": False,
            "records_location": "post_detection_gui_validation",
        },
        "post_detection_gui_validation": gui_validation_records,
        "user_validation_guide": {
            "gui_translate_semantics": (
                "A prim's GUI Translate is its world-space origin or center, "
                "not camera distance."
            ),
            "measurement_semantics": (
                "The representative distance and XYZ refer to one visible "
                "surface sample, never the hidden object center. Use the "
                "extent, depth profile, and region label mask for the full "
                "visible surface."
            ),
            "plane_comparison": (
                "Use point_world_xyz_m and the plane equation for any plane. "
                "For an axis-aligned plane, compare constant_world_axis with "
                "the matching GUI surface coordinate, not automatically with "
                "the prim center. Account for half thickness."
            ),
        },
        "limitations": [
            "Touching surfaces without a measurable depth discontinuity may merge.",
            "Curved or steeply sloped surfaces may split if thresholds are too strict.",
            "A region is a visible surface and does not by itself identify an object class.",
        ],
    }
    quick_items = []
    for record in target_records:
        quick_item = {
            "rank": len(quick_items) + 1,
            "surface_id": record["region_id"],
            "type_hint": record["semantic_hint"],
            "distance_to_camera_m": record["distance_m"][
                "camera_to_representative_surface"
            ],
            "surface_camera_xyz_m": record["coordinates_m"][
                "surface_camera_xyz"
            ],
            "surface_world_xyz_m": record["coordinates_m"][
                "surface_world_xyz"
            ],
            "image_bbox_px": record["visibility"]["bbox_px"],
            "visible_camera_range_m": record["surface_depth_profile_m"][
                "euclidean_camera_range"
            ],
            "visible_world_aabb_m": record["visible_surface_extent_m"][
                "world_axis_aligned"
            ],
            "surface_model_kind": record["surface_model"]["kind"],
        }
        if record["surface_model"]["kind"] == "plane":
            quick_item["plane"] = {
                "normal_world_unit": record["surface_model"][
                    "normal_world_unit"
                ],
                "point_world_xyz_m": record["surface_model"][
                    "point_world_xyz_m"
                ],
                "equation": record["surface_model"]["equation"],
                "camera_perpendicular_distance_m": record["surface_model"][
                    "camera_perpendicular_distance_m"
                ],
            }
            if "constant_world_axis" in record["surface_model"]:
                quick_item["plane"]["constant_world_axis"] = record[
                    "surface_model"
                ]["constant_world_axis"]
        quick_items.append(quick_item)
    target_annotations = _write_visual_validation(
        capture_directory, target_records, label_image
    )
    measurement["visual_validation"] = {
        "pixel_coordinate_origin": "top-left",
        "pixel_axes": {"u": "right", "v": "down"},
        "target_selection": (
            "reported_targets_near_to_far only; known floor regions are excluded"
        ),
        "rgb_markers": "rgb_left_annotated.png",
        "depth_markers": "depth_preview_annotated.png",
        "depth_marker_value": (
            "representative axial Z-forward depth in metres at the same pixel "
            "marked in rgb_left_annotated.png"
        ),
        "target_overlay": "region_overlay.png",
        "marker_legend": target_annotations,
    }
    output_path = os.path.join(capture_directory, "measurements.json")
    with open(output_path, "w", encoding="utf-8") as output:
        json.dump(measurement, output, indent=2)

    quick_measurement = {
        "schema": "d455-visible-targets-summary-v3",
        "capture_id": capture_metadata["run_id"],
        "source_report": "measurements.json",
        "important": (
            "GUI Translate is a world-space prim center/origin. "
            "distance_to_camera_m is camera-to-visible-surface range."
        ),
        "ordering": (
            "Euclidean norm of the reported surface_camera_xyz_m, "
            "nearest to farthest"
        ),
        "excluded_environment_hints": ["likely_floor"],
        "counts": {
            "sensor_region_count": len(region_records),
            "reported_target_count": len(quick_items),
            "excluded_environment_region_count": len(environment_records),
        },
        "visible_targets_near_to_far": quick_items,
        "annotated_images": {
            "rgb": "rgb_left_annotated.png",
            "depth": "depth_preview_annotated.png",
            "target_overlay": "region_overlay.png",
        },
    }
    quick_output_path = os.path.join(capture_directory, "summary.json")
    with open(quick_output_path, "w", encoding="utf-8") as output:
        json.dump(quick_measurement, output, indent=2)
    summary = {
        "status": "pass",
        "capture_id": capture_metadata["run_id"],
        "sensor_region_count": len(region_records),
        "reported_target_count": len(quick_items),
        "excluded_environment_region_count": len(environment_records),
        "output": output_path,
        "summary_output": quick_output_path,
    }
    print(summary)
    return summary


def demo_measure_depth_capture(*args, **kwargs):
    """Compatibility alias for the unified depth-first measurement report."""
    return demo_measure_capture(*args, **kwargs)


def demo_capture(label=None, hide_ik_target=True):
    """Capture a uniquely named D455 snapshot; ``label`` is optional.

    The IK target is hidden in the USD session layer for the rendered frame and
    restored in a ``finally`` block. The scene's root layer is never saved.
    """
    import omni.kit.app
    import omni.timeline
    from pxr import Usd, UsdGeom

    setup = demo_capture_setup()
    _, stage, stage_path, output_root = _active_stage_context()
    stage_sha256_before = _sha256(stage_path)
    run_id, run_dir, timestamp, safe_label, sequence = _create_unique_run_dir(
        output_root, label
    )
    registry = _registry()
    annotators = registry["annotators"]
    app = omni.kit.app.get_app()
    timeline = omni.timeline.get_timeline_interface()

    target_imageable = None
    previous_visibility = None
    if hide_ik_target:
        target = stage.GetPrimAtPath(IK_TARGET_PATH)
        if target.IsValid() and target.IsA(UsdGeom.Imageable):
            target_imageable = UsdGeom.Imageable(target)
            previous_visibility = target_imageable.GetVisibilityAttr().Get()
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                target_imageable.GetVisibilityAttr().Set(UsdGeom.Tokens.invisible)

    try:
        settle = _wait_for_ik_settle()
        for _ in range(5):
            app.update()
        render_method = _force_render_step()
        rgb = {}
        rgb_diagnostics = {}
        for eye in ("left", "right", "color"):
            rgb[eye], rgb_diagnostics[eye] = _read_rgb_with_retry(
                annotators[eye]["rgb"]
            )
        axial_left = np.asarray(
            annotators["left"]["distance_to_image_plane"].get_data(),
            dtype=np.float32,
        )
        radial_left = np.asarray(
            annotators["left"]["distance_to_camera"].get_data(),
            dtype=np.float32,
        )
        axial_right = np.asarray(
            annotators["right"]["distance_to_image_plane"].get_data(),
            dtype=np.float32,
        )
    finally:
        if target_imageable is not None:
            restored = previous_visibility or UsdGeom.Tokens.inherited
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                target_imageable.GetVisibilityAttr().Set(restored)

    _save_png(rgb["color"], os.path.join(run_dir, "rgb_color.png"))
    _save_png(rgb["left"], os.path.join(run_dir, "rgb_left.png"))
    _save_png(rgb["right"], os.path.join(run_dir, "rgb_right.png"))
    np.save(os.path.join(run_dir, "depth_axial_left.npy"), axial_left)
    np.save(os.path.join(run_dir, "depth_radial_left.npy"), radial_left)
    np.save(os.path.join(run_dir, "depth_axial_right.npy"), axial_right)
    _save_png(_depth_preview(axial_left), os.path.join(run_dir, "depth_preview.png"))

    frames = {name: _camera_frame(stage, path) for name, path in CAMERA_PATHS.items()}
    baseline = float(
        np.linalg.norm(
            np.asarray(frames["left"]["position_m"])
            - np.asarray(frames["right"]["position_m"])
        )
    )
    valid_depth = np.isfinite(axial_left) & (axial_left > 0)
    failures = [
        f"{eye} RGB is black or invalid"
        for eye, diagnostic in rgb_diagnostics.items()
        if not diagnostic["valid"]
    ]
    if not settle.get("settled", False):
        failures.append(
            "IK target did not converge before capture timeout"
        )
    if not np.any(valid_depth):
        failures.append("left axial depth contains no finite positive samples")
    if abs(baseline - 0.095) > 0.002:
        failures.append(f"stereo baseline {baseline:.6f} m is outside tolerance")
    stage_sha256_after = _sha256(stage_path)
    if stage_sha256_after != stage_sha256_before:
        failures.append("the root USD changed during capture")
    target_visibility_after = None
    target_after = stage.GetPrimAtPath(IK_TARGET_PATH)
    if target_after.IsValid() and target_after.IsA(UsdGeom.Imageable):
        target_visibility_after = str(
            UsdGeom.Imageable(target_after).GetVisibilityAttr().Get()
            or UsdGeom.Tokens.inherited
        )

    metadata = {
        "schema": "d455-demo-capture-v1",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "run_id": run_id,
        "timestamp_utc": timestamp,
        "daily_sequence": sequence,
        "label": safe_label,
        "stage": {
            "path": stage_path,
            "sha256_before": stage_sha256_before,
            "sha256_after": stage_sha256_after,
            "unchanged_during_capture": stage_sha256_after == stage_sha256_before,
        },
        "output_directory": run_dir,
        "resolution": {"width": WIDTH, "height": HEIGHT},
        "timeline_playing": timeline.is_playing(),
        "ik_settle": settle,
        "ik_target_hidden_during_capture": target_imageable is not None,
        "ik_target_visibility_after_capture": target_visibility_after,
        "render_method": render_method,
        "rgb_readback": rgb_diagnostics,
        "camera_frames": frames,
        "stereo_baseline_m": baseline,
        "depth": {
            "axial_semantics": "distance_to_image_plane",
            "radial_semantics": "distance_to_camera",
            "left_valid_pixel_count": int(valid_depth.sum()),
        },
        "setup": setup,
    }
    with open(os.path.join(run_dir, "capture.json"), "w", encoding="utf-8") as output:
        json.dump(metadata, output, indent=2)

    try:
        measurement_summary = demo_measure_capture(run_dir, stage=stage)
    except Exception as error:
        measurement_summary = {"status": "fail", "error": repr(error)}
        failures.append(f"visible-surface measurement failed: {error!r}")
    metadata["measurement"] = measurement_summary
    metadata["failures"] = failures
    metadata["status"] = "pass" if not failures else "fail"
    with open(os.path.join(run_dir, "capture.json"), "w", encoding="utf-8") as output:
        json.dump(metadata, output, indent=2)

    summary = {
        "status": metadata["status"],
        "run_id": run_id,
        "output_directory": run_dir,
        "label": safe_label,
        "failures": failures,
    }
    registry["last_summary"] = summary
    print(summary)
    return summary


def demo_capture_status():
    """Return the latest capture summary for this Isaac Sim process."""
    return _registry()["last_summary"]
