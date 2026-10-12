"""Precomp caching, v2.

A precomp is a PrecompWrite (a plain Write, `reading` off) followed by a
switch group routing either to the live upstream or to a Read of a
previously rendered version of that Write ("cache").

Principles:
  * Decisions are made in the GUI at well-defined moments (refresh,
    submit) and stored as plain knob values — no Python expression, no
    render hook, no graph mutation on the farm. The farm renders exactly
    the script that was saved.
  * A cache is valid when its manifest (precomp.json, next to the frames)
    records the current upstream content hash and every needed frame is
    on disk.
  * The content hash is a Merkle hash of the upstream graph (knob values
    + input topology + expression links), independent of node names and
    of evaluation state.

Modules:
    spec      names, markers, schema
    manifest  precomp.json I/O, version folders, frames on disk (no nuke)
    hashing   upstream content hash
    nodes     discovery, switch construction/routing, legacy upgrade
    engine    evaluate / sync / prepare renders
    watcher   GUI callbacks re-syncing switches after upstream edits
"""
