import nuke, os, json, tempfile

def _write_render_state():
    n = nuke.thisNode()
    renderpath = n.knob('renderpath').value()
    folder = os.path.dirname(renderpath)
    if not folder:
        return
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)

    state_path = os.path.join(folder, 'render_state.json')
    data = {"Render_Done": True}

    fd, tmp_path = tempfile.mkstemp(dir=folder, prefix='.render_state_', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=4)
        os.replace(tmp_path, state_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

_write_render_state()