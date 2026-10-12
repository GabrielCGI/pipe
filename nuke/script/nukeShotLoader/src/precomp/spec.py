"""Names and markers of the precomp system (no nuke import)."""

SCHEMA = 2

PRECOMP_TAG = "PrecompWrite"        # value of the Write `tag` knob (shared with v1)
WRITE_MARKER = "precomp_write"      # Int knob on v2 PrecompWrites (= SCHEMA)
SWITCH_MARKER = "precomp_switch"    # Int knob on v2 switch groups (= SCHEMA)
# Int knob on a PrecompWrite set by "Force Live" (the version it moved to).
# Part of the content hash when set: every render made before no longer
# matches, for this precomp and the precomps downstream of it.
LIVE_FROM = "precomp_live_from"
# Hidden String knob: "<live_from> <versions>" before the last Force Live,
# restored when it is cancelled before its version is rendered.
FORCE_UNDO = "precomp_force_undo"

# Switch group knobs / internal node names.
WHICH = "which"                     # 0 = live, 1 = cache
LIVE, CACHE = 0, 1                  # default 0 (not even written in the .nk) is the safe side
STATUS_KNOB = "precomp_status"
CACHE_FILE_KNOB = "cache_file"
CACHE_READ = "CacheRead"
INNER_SWITCH = "Switch"
INNER_INPUT = "Input"
INNER_OUTPUT = "Output"

# v1 (expression-driven) setups.
LEGACY_WHICH = "which_custom"
LEGACY_SCRIPTS = ("before_render_precomp", "after_render_precomp", "after_compo_render_diagnostic")

TILE_COLORS = {"cached": 0x3a5a3aff, "live": 0xaa2c2cff}

# Prism's own beforeRender on compo Writes (restored when a v1 hook is removed).
PRISM_COMPO_BEFORE_RENDER = "try: pcore.appPlugin.getOutputPath(nuke.thisNode(), render=True)\nexcept: pass"
# ... and its afterRender: Prism marks the Write "rendering" in its beforeRender, this clears
# the mark (while marked, Prism's refresh keeps returning that render's path).
PRISM_COMPO_AFTER_RENDER = "try: pcore.appPlugin.finishedRendering(nuke.thisNode())\nexcept: pass"
RENDER_BUTTON_SCRIPT = "from src.ui import write_render\nwrite_render.render_write(nuke.thisNode())"
PREVIOUS_VERSION_BUTTON_SCRIPT = ("from src.ui import write_render\n"
                                  "write_render.render_previous_version(nuke.thisNode())")
# Buttons replaced by the two above when the Writes are upgraded: Prism's own
# (Compo Writes) and the earlier v2 PrecompWrite Render.
FORMER_RENDER_BUTTONS = ("pcore.appPlugin.startRender(nuke.thisNode())",
                         "from src.precomp import engine\nengine.render_locally(nuke.thisNode())")
FORMER_PREVIOUS_VERSION_BUTTONS = ("pcore.appPlugin.renderAsVersion(nuke.thisNode())",)
# Prism's checkbox next to the Render button: ticked = farm submission.
SUBMIT_JOB = "submitJob"
# Prism tab knobs hidden on the Shot Loader's Writes (values kept): Prism's
# unused ones, and the precomp version controls (shown locked below).
HIDDEN_TAB_KNOBS = ("comment", "location", "fileName", "refresh", "prevFileName", "openDir", "createRead",
                    "media_conversion_divider", "media_conversion_use", "media_conversion_preset",
                    "media_conversion_refresh", "media_conversion_edit",
                    "project_management_divider", "project_management_publish",
                    "versions", "add_version", "sub_version")
# Read-only block at the bottom of the Prism tab: version (locked, follows
# the output), output path (live label), Open In Explorer.
INFO_DIVIDER = "render_info_divider"
VERSION_DISPLAY = "render_version"
OUTPUT_DISPLAY = "render_output"
OPEN_BUTTON = "open_in_explorer"
PRECOMP_VERSION_EXPRESSION = "[value versions]"
# The digits ending the version folder of Prism's fileName ('.../v038/...' -> 38), 0 without.
COMPO_VERSION_EXPRESSION = ("[scan [lindex [concat [regexp -inline {[0-9]+$} "
                            "[file tail [file dirname [value fileName]]]] 0] 0] %d]")
OUTPUT_DISPLAY_COMMAND = "__import__('src.ui.knob_widgets', fromlist=['OutputPath']).OutputPath(nuke.thisNode())"
OPEN_BUTTON_SCRIPT = "from src.ui import write_render\nwrite_render.open_in_explorer(nuke.thisNode())"
