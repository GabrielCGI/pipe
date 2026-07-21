# beforeRender hook: intentionally a no-op.
#
# Previously this reset render_state.json to {"Render_Done": False} at the
# start of each Deadline task. Tasks run in parallel across workers, so a
# task starting mid-render would race-clobber a True written by a peer
# task that had already finished — leaving render_state.json stuck at
# False even though the render completed successfully.
#
# The reset is now performed exactly once at submit time, in
# ui_loader_simple._reset_render_states, before any Deadline task starts.
# Combined with after_render_precomp.py being monotonic (True-only), this
# guarantees the state can only progress False -> True and never race
# backwards.
#
# This file is kept as an empty hook so that any Write node whose
# beforeRender knob still references it continues to execute cleanly.
