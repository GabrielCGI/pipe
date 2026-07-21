import nuke, os
import module_precomp as mp

def _write_render_state():
    n = nuke.thisNode()
    folder = os.path.dirname(n['renderpath'].value())
    if not folder:
        return
    os.makedirs(folder, exist_ok=True)

    # Only ever write True from here — never False. On Deadline, tasks
    # run in parallel across workers, so this hook fires N times
    # concurrently. Making the write monotonic (True-only) means the
    # last task that observes a complete render wins, and no laggard
    # can undo completion. The reset to False happens exactly once, at
    # submit time (ui_loader_simple._reset_render_states), before any
    # task starts.
    #
    # Even monotonic writes can leave the state stuck at False when the
    # last task's all_present check races the network share; that case
    # is handled by _compute_which's self-heal, not here.
    if mp._all_frames_present(n):
        mp._atomic_json(os.path.join(folder, "render_state.json"),
                        {"Render_Done": True})

_write_render_state()