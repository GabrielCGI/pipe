import hou


def is_cop_network(node: hou.Node) -> bool:
    """Return True if the node behaves like a COP network."""
    cat = node.childTypeCategory()
    if cat is None:
        return False
    return cat.name().lower().startswith("cop")


def ensure_live_parm(copnet: hou.Node) -> None:
    """Ensure toggle 'live' exists."""
    if copnet.parm("live") is not None:
        return

    ptg = copnet.parmTemplateGroup()
    live_parm = hou.ToggleParmTemplate("live", "Live", default_value=True)
    ptg.append(live_parm)
    copnet.setParmTemplateGroup(ptg)


def ensure_version_parm(copnet: hou.Node) -> None:
    """Ensure an int slider 'version' exists on the COP net."""
    if copnet.parm("version") is not None:
        return

    ptg = copnet.parmTemplateGroup()
    version_parm = hou.IntParmTemplate(
        "version",
        "Version",
        1,
        default_value=(1,),
        min=1,
        max=999,
    )
    ptg.append(version_parm)
    copnet.setParmTemplateGroup(ptg)


def ensure_bake_button(copnet: hou.Node) -> None:
    """Add 'Render to Disk' button that renders and then reloads the file."""
    if copnet.parm("execute") is not None:
        return

    ptg = copnet.parmTemplateGroup()

    button = hou.ButtonParmTemplate("execute", "Render to Disk")

    # 1. Set live = 0
    # 2. Trigger BAKE_ROP.execute
    # 3. Trigger BAKE_READ.reload
    callback = (
        'node = hou.pwd()\n'
        'live = node.parm("live")\n'
        'if live is not None:\n'
        '    live.set(0)\n'
        'rop = node.node("BAKE_ROP")\n'
        'if rop is not None and rop.parm("execute") is not None:\n'
        '    rop.parm("execute").pressButton()\n'
        'reader = node.node("BAKE_READ")\n'
        'if reader is not None:\n'
        '    reload_parm = reader.parm("reload")\n'
        '    if reload_parm is not None:\n'
        '        reload_parm.pressButton()\n'
    )
    button.setScriptCallback(callback)
    button.setScriptCallbackLanguage(hou.scriptLanguage.Python)

    tags = {
        "import_token": "execute",
        "autoscope": "0000000000000000",
        "takecontrol": "always",
    }
    button.setTags(tags)

    ptg.append(button)
    copnet.setParmTemplateGroup(ptg)


def setup_reader(reader: hou.Node) -> None:
    """
    Configure the file COP reader:
    - filename  = chs("../BAKE_ROP/copoutput")
    - aovs      = 1
    - aov1      = "C"
    """
    filename_expr = 'chs("../BAKE_ROP/copoutput")'

    p = reader.parm("filename")
    if p is not None:
        p.setExpression(filename_expr, language=hou.exprLanguage.Hscript)

    p = reader.parm("aovs")
    if p is not None:
        p.set(1)

    p = reader.parm("aov1")
    if p is not None:
        p.set("C")


def process_cop(copnet: hou.Node) -> None:
    """Main processor for a single COP network."""
    if copnet is None or not is_cop_network(copnet):
        return

    out = copnet.node("OUT_HDRI_01")
    if out is None:
        return

    # Ensure UI parms exist first (so expressions can refer to them)
    ensure_live_parm(copnet)
    ensure_version_parm(copnet)

    # --- Create / find nodes ---
    # Use version in the filename:
    # $HIP/hdri_cop/<copnet_name>_v###.exr
    exr_expr = '$HIP/hdri_cop/`opname("..")`_v`padzero(3,ch("../version"))`.exr'

    rop = copnet.node("BAKE_ROP")
    if rop is None:
        rop = copnet.createNode("rop_image", "BAKE_ROP")

    reader = copnet.node("BAKE_READ")
    if reader is None:
        reader = copnet.createNode("file", "BAKE_READ")

    switch = copnet.node("OUT_HDRI_SWITCH")
    if switch is None:
        switch = copnet.createNode("switch", "OUT_HDRI_SWITCH")

    # --- Configure ROP ---
    rop.parm("copoutput").set(exr_expr)

    # --- Detect live input in an idempotent way ---
    live_input = None

    # 1) If switch already has input 1, that is the live network.
    sw_inputs = switch.inputs()
    if len(sw_inputs) > 1 and sw_inputs[1] is not None:
        live_input = sw_inputs[1]
    else:
        # 2) Otherwise, try the OUT_HDRI_01's current input,
        #    but only if it's not the switch itself.
        out_inputs = out.inputs()
        if out_inputs:
            candidate = out_inputs[0]
            if candidate is not switch:
                live_input = candidate

    # Set the ROP's coppath based on live_input
    if live_input is not None:
        rop.parm("coppath").set(live_input.path())
    else:
        rop.parm("coppath").set("")

    # --- Configure reader ---
    setup_reader(reader)

    # --- Wire switch safely (no recursion) ---

    # input 0 = baked file (reader)
    switch.setInput(0, reader)

    # If we just discovered a live_input that isn't already wired, wire it to input 1.
    if live_input is not None:
        sw_inputs = switch.inputs()
        current_live = sw_inputs[1] if len(sw_inputs) > 1 else None
        if current_live is None:
            # Only rewire OUT_HDRI_01 if its input is that live_input
            out_inputs = out.inputs()
            if out_inputs and out_inputs[0] is live_input:
                out.setInput(0, None)
            switch.setInput(1, live_input)

    # Ensure OUT_HDRI_01 is driven by the switch (but don't create loops)
    out_inputs = out.inputs()
    if not out_inputs or out_inputs[0] is not switch:
        out.setInput(0, switch)

    # --- Live toggle drives switch ---
    switch.parm("input").setExpression('ch("../live")', language=hou.exprLanguage.Hscript)

    # --- Bake button (render + reload + set live off) ---
    ensure_bake_button(copnet)

    # Layout
    reader.moveToGoodPosition()
    switch.moveToGoodPosition()
    rop.moveToGoodPosition()


def run() -> None:
    """Process all selected COP networks."""
    selected = hou.selectedNodes()
    if not selected:
        return

    with hou.undos.group("Setup HDRI COP Bake"):
        for node in selected:
            if is_cop_network(node):
                process_cop(node)
