"""
reconnect_postage_stamps.py
----------------------------
Parcourt tous les PostageStamp de la scène Nuke,
et exécute le knob 'reconnect_by_title_similar' s'il existe.
"""

import contextlib

import nuke


@contextlib.contextmanager
def _suppress_nuke_message():
    """Remplace temporairement `nuke.message` par un no-op qui logge en console.

    Permet de museler les popups émis par le plugin Stamps interne lors de
    `knob.execute()` (ex: "No Anchor Stamps with title '{}' found").
    """
    original = nuke.message

    def _silent(msg):
        print("[reconnect_stamps] suppressed nuke.message: {}".format(msg))

    nuke.message = _silent
    try:
        yield
    finally:
        nuke.message = original


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
                # Exécute le Python Script Button knob.
                # En silent, on muselle les popups émis par le plugin Stamps
                # (ex: "No Anchor Stamps with title '{}' found in the script").
                if silent:
                    with _suppress_nuke_message():
                        knob.execute()
                else:
                    knob.execute()
                executed.append(node.name())
            except Exception as e:
                nuke.warning(
                    "Erreur sur '{}' : {}".format(node.name(), str(e))
                )
                skipped.append("{} (erreur: {})".format(node.name(), str(e)))
        else:
            skipped.append("{} (knob absent)".format(node.name()))

    # Log console court — pas de liste détaillée
    print(
        "[reconnect_stamps] {} exécutés, {} ignorés (total {})".format(
            len(executed), len(skipped), len(postage_stamps)
        )
    )

    if not silent:
        # Popup détaillé uniquement en mode interactif
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
        nuke.message("\n".join(report_lines))

    return executed, skipped


# Point d'entrée standalone — exécuté uniquement quand le fichier est lancé
# directement, pas quand il est importé par le loader.
if __name__ == "__main__":
    run_reconnect_on_postage_stamps()