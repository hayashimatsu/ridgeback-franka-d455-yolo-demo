"""One-step GUI bootstrap for the Ridgeback + Panda + D455 demo.

Open the demo USD, press Play, open this file in Isaac Sim's Script Editor,
and press Ctrl+Enter. The script loads the local IK and capture modules, starts
one IK callback, and exposes ``demo_capture()`` in the Script Editor globals.
Re-running this file safely replaces the previous IK callback.
"""

import os


def _demo_project_root():
    import omni.usd

    stage = omni.usd.get_context().get_stage()
    if stage is None:
        raise RuntimeError("No USD stage is open.")
    layer = stage.GetRootLayer()
    stage_path = layer.realPath or layer.identifier
    if not stage_path or not os.path.isfile(stage_path):
        raise RuntimeError("Open the saved local demo USD before running this script.")
    return os.path.dirname(os.path.dirname(os.path.abspath(stage_path)))


def _execute_local_script(path):
    with open(path, "r", encoding="utf-8") as source:
        code = compile(source.read(), path, "exec")
    exec(code, globals())


def demo_start():
    import omni.kit.app
    import omni.timeline
    import omni.usd

    root = _demo_project_root()
    stage = omni.usd.get_context().get_stage()
    required_prims = [
        "/World/ridgeback_franka",
        "/World/ridgeback_franka/panda_hand",
        "/World/IKTarget",
    ]
    missing = [path for path in required_prims if not stage.GetPrimAtPath(path).IsValid()]
    if missing:
        raise RuntimeError(f"The active stage is not the demo scene; missing: {missing}")

    timeline = omni.timeline.get_timeline_interface()
    if not timeline.is_playing():
        timeline.play()
    app = omni.kit.app.get_app()
    for _ in range(5):
        app.update()

    _execute_local_script(os.path.join(root, "scripts", "ik_controller.py"))
    _execute_local_script(os.path.join(root, "scripts", "capture_d455.py"))
    ik_result = ik_follow_start()
    capture_result = demo_capture_setup()
    result = {
        "status": "ready",
        "project_root": root,
        "ik": ik_result,
        "capture": capture_result,
        "next_action": (
            "Drag /World/IKTarget, then call demo_capture(); color and depth "
            "measurement JSON files are created automatically."
        ),
    }
    print(result)
    return result


def demo_stop():
    """Stop the IK callback and restore the validated static arm pose."""
    result = ik_follow_stop()
    print(result)
    return result


DEMO_START_RESULT = demo_start()
