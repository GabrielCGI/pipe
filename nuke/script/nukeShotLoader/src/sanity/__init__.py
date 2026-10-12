"""Sanity check run before a Render Manager submission.

    rules.py   the rules: each one checks the nodes a render depends on,
               lists the offending nodes and knows how to fix them
    (ui/sanity_dialog.py runs them one by one, with Fix / Close)

Adding a rule: subclass rules.Rule and add it to rules.RULES.
"""
