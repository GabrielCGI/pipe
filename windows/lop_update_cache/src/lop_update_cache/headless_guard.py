"""
headless_guard.py - aucune fenetre modale ne doit pouvoir geler un moteur headless.

En hython / mayapy, personne ne cliquera : un `QDialog.exec()` attend pour toujours
(process gele, CPU a zero). Vu en vrai avec le sanity_check studio, que le hook
`prePublish` lance a CHAQUE publish Prism (export, cache, submit de render) : des qu'un
check echoue, il ouvre `MainDialog.exec()`.

`install()` remplace exec() par une reponse AUTOMATIQUE qui suit la regle de la GUI :
  - sanity_check avec une ERROR -> refus : en GUI 'Publish anyways' est GRISE ;
  - sanity_check avec des WARNINGS seulement -> accepte : la GUI laisse publier ;
  - toute autre fenetre modale -> refusee (Cancel).
Chaque reponse est loguee ET gardee dans `DIALOGS`, pour que l'appelant sache qu'un
publish a ete refuse (sinon un publish annule ressemble a un succes : pas d'erreur sur
le node, juste rien d'ecrit).

Pur Qt : pas de hou, pas de maya -> testable hors DCC.
"""

DIALOGS = []  # une entree par fenetre modale interceptee (ordre chronologique)


def _call(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def failed_checks(dialog):
    """Checks en echec d'une fenetre sanity_check studio : [{label, severity, message}]."""
    out = []
    for c in getattr(dialog, "failed_check", None) or []:
        sev = getattr(getattr(c, "severity", None), "name", None) or str(
            getattr(c, "severity", "?")
        )
        msg = " ".join((getattr(c, "message", "") or "").split())
        out.append({"label": getattr(c, "label", "?"), "severity": sev, "message": msg})
    return out


def refused_since(start):
    """Fenetres REFUSEES depuis l'index `start` de DIALOGS (sanity ERROR ou autre)."""
    return [d for d in DIALOGS[start:] if not d.get("accepted")]


def describe(entry):
    """Texte court d'une fenetre refusee, pour un message d'erreur."""
    errors = [c for c in entry.get("sanity") or [] if c["severity"] == "ERROR"]
    if errors:
        return "sanity check ERROR : %s" % ", ".join(c["label"] for c in errors)
    return "fenetre '%s' refusee" % entry.get("title", "?")


def install(log):
    """Installe le garde-fou (idempotent : un 2e appel ne re-patche pas). `log(str)`
    recoit chaque decision. Retourne la liste des methodes patchees."""
    try:
        from PySide6 import QtWidgets
    except ImportError:
        from PySide2 import QtWidgets

    if getattr(QtWidgets.QDialog, "_lop_headless_guard", False):
        return []

    def _exec(self, *a, **k):
        title = _call(self.windowTitle, "") or type(self).__name__
        if hasattr(self, "failed_check"):  # le sanity_check studio
            checks = failed_checks(self)
            errors = [c for c in checks if c["severity"] == "ERROR"]
            answer = 0 if errors else 1
            for c in checks:
                log(
                    "  sanity check %s : %s -- %s"
                    % (c["severity"], c["label"], c["message"] or "-")
                )
            log(
                "  sanity check : %s (%d erreur(s), %d warning(s))"
                % (
                    "REFUS, comme la GUI" if errors else "warnings seuls -> publie",
                    len(errors),
                    len(checks) - len(errors),
                )
            )
            DIALOGS.append({"title": title, "sanity": checks, "accepted": bool(answer)})
            return answer
        log("  fenetre modale '%s' refusee (headless : personne pour cliquer)" % title)
        DIALOGS.append({"title": title, "accepted": False})
        return 0

    def _static_box(*a, **k):
        text = " | ".join(x for x in a if isinstance(x, str))  # titre | message
        log(
            "  QMessageBox statique refusee en headless : %s"
            % " ".join(text.split())[:300]
        )
        DIALOGS.append({"title": "QMessageBox", "text": text, "accepted": False})
        return QtWidgets.QMessageBox.StandardButton.Cancel

    def _get_text(*a, **k):
        # QInputDialog.getText : (texte, ok). ok=False = l'utilisateur a annule.
        label = " | ".join(x for x in a if isinstance(x, str))
        log("  QInputDialog refusee en headless : %s" % " ".join(label.split())[:200])
        DIALOGS.append({"title": "QInputDialog", "text": label, "accepted": False})
        return "", False

    patched = []
    for cls in (QtWidgets.QDialog, QtWidgets.QMessageBox):
        for name in ("exec", "exec_"):
            if hasattr(cls, name):
                try:
                    setattr(cls, name, _exec)
                    patched.append("%s.%s" % (cls.__name__, name))
                except Exception as e:
                    log(
                        "  (garde-fou : %s.%s non patchable : %s)"
                        % (cls.__name__, name, e)
                    )
    for name in ("information", "warning", "critical", "question"):
        try:
            setattr(QtWidgets.QMessageBox, name, staticmethod(_static_box))
            patched.append("QMessageBox.%s" % name)
        except Exception as e:
            log("  (garde-fou : QMessageBox.%s non patchable : %s)" % (name, e))
    try:
        QtWidgets.QInputDialog.getText = staticmethod(_get_text)
        patched.append("QInputDialog.getText")
    except Exception as e:
        log("  (garde-fou : QInputDialog.getText non patchable : %s)" % e)
    QtWidgets.QDialog._lop_headless_guard = True
    log(
        "garde-fou headless : aucune fenetre modale ne peut bloquer (%s)"
        % ", ".join(patched)
    )
    return patched
