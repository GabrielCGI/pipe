"""
reconnect_postage_stamps.py
----------------------------
Parcourt tous les PostageStamp de la scène Nuke,
et exécute le knob 'reconnect_by_title_similar' s'il existe.
"""

import nuke


def run_reconnect_on_postage_stamps(silent=False):
    """Exécute `reconnect_by_title_similar` sur tous les PostageStamp du script.

    Args:
        silent (bool): si True, supprime les popups `nuke.message` (le rapport
            reste dans la console). Utile quand l'appel est chaîné après un
            autre flow qui a déjà son propre feedback.

    Returns:
        tuple: (executed, skipped) — listes de noms de nodes.
    """
    postage_stamps = [n for n in nuke.allNodes() if n.Class() == "PostageStamp"]

    if not postage_stamps:
        if not silent:
            nuke.message("Aucun PostageStamp trouvé dans la scène.")
        return [], []

    executed = []
    skipped = []

    for node in postage_stamps:
        knob = node.knob("reconnect_by_title_similar")

        if knob is not None:
            try:
                # Exécute le Python Script Button knob
                knob.execute()
                executed.append(node.name())
            except Exception as e:
                nuke.warning(
                    "Erreur sur '{}' : {}".format(node.name(), str(e))
                )
                skipped.append("{} (erreur: {})".format(node.name(), str(e)))
        else:
            skipped.append("{} (knob absent)".format(node.name()))

    # Rapport final
    report_lines = [
        "=== Reconnect PostageStamps ===",
        "",
        "Total PostageStamps : {}".format(len(postage_stamps)),
        "Exécutés            : {}".format(len(executed)),
        "Ignorés             : {}".format(len(skipped)),
    ]

    if executed:
        report_lines += ["", "✔ Exécutés :"] + ["  - {}".format(n) for n in executed]

    if skipped:
        report_lines += ["", "✘ Ignorés :"] + ["  - {}".format(n) for n in skipped]

    report = "\n".join(report_lines)
    print(report)
    if not silent:
        nuke.message(report)

    return executed, skipped


# Point d'entrée standalone — exécuté uniquement quand le fichier est lancé
# directement, pas quand il est importé par le loader.
if __name__ == "__main__":
    run_reconnect_on_postage_stamps()