# -*- coding: utf-8 -*-
r"""
recache_maya.py - Moteur MAYA : met a jour les rigs perimes d'une scene d'anim, puis
execute ses exports Prism.

Pendant de recache_cfx.py (qui tourne dans hython) : celui-ci tourne dans **mayapy**.
Il ne partage que la detection de version (preview.py) et la lecture des references et
des states (maya_refs.py). Il ne touche a RIEN du chemin Houdini.

Sequence (validee avec Thomas) :  update -> VERIFIER -> incrementer -> exporter
  1. `--status`  : quels rigs sont perimes, quels exports existent. AUCUN Maya : lecture
                   texte du .ma.
  2. `--apply`   : ouvre la scene dans mayapy, swappe les references choisies, puis
                   MESURE ce qui a ete perdu (droit de veto).
  3. version-up Prism de la scene (sauf `--no-save` ; `--save-as` = copie locale).
  4. `--export <uuid...>` : execute ces states d'export du State Manager Prism, comme un
     clic droit > Execute. Les hooks studio tournent a l'identique (postExport ->
     usd_chaser sur les `_layer_anm_*`) : mayapy lit Maya.env (MAYA_ENV_DIR), le
     PYTHONPATH studio est donc la (verifie : `import usd_chaser` OK).

/!\ LE PIEGE, et la raison d'etre de l'etape 2 : swapper un rig dont un controleur a ete
renomme ou supprime ne produit AUCUNE erreur. Maya charge la reference et transforme
l'animation posee dessus en **failed edits**, silencieusement. On compare donc le nombre
d'edits en echec AVANT et APRES, et on REFUSE d'incrementer ET d'exporter si ca a
augmente : mieux vaut ne rien livrer qu'une anim amputee qui a l'air parfaite.

La fin d'un --apply emet TOUJOURS un bloc MAYA_RESULT (json) : l'UI lit ce verdict
plutot que le code de sortie, qu'un Maya qui se ferme mal peut fausser. Pas de bloc =
le process est mort en route (crash Maya) -> "non traitable", jamais un succes.
"""

import argparse
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(_HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(_HERE))

from lop_update_cache import maya_refs, preview  # noqa: E402

_START = time.perf_counter()

STATUS_START = ">>>STATUS_JSON>>>"
STATUS_END = "<<<STATUS_JSON<<<"
EXPORTS_START = ">>>EXPORTS_JSON>>>"
EXPORTS_END = "<<<EXPORTS_JSON<<<"
SAVED_START = ">>>SAVED_SCENE>>>"
SAVED_END = "<<<SAVED_SCENE<<<"
RESULT_START = ">>>MAYA_RESULT>>>"
RESULT_END = "<<<MAYA_RESULT<<<"

# suffixe du commentaire quand la scene n'est pas sauvee : meme regle que les renders
# Houdini -> on sait, en lisant le produit, que sa scene source ne contient pas l'update
NOT_SAVED_SUFFIX = " (scene not saved)"


def log(msg):
    print(
        "[recache_maya] [%6.1fs] %s" % (time.perf_counter() - _START, msg), flush=True
    )


def _vlabel(v):
    return ("v%03d" % v) if isinstance(v, int) and v >= 0 else None


# --------------------------------------------------------------------------- #
#  STATUS : sans Maya
# --------------------------------------------------------------------------- #
def status(scene):
    """[{asset, product, version, latest, stale, refs:[ns...]}] -- un item par ASSET."""
    if not maya_refs.is_ascii_maya(scene):
        log("scene illisible en texte (binaire .mb ?) : detection impossible sans Maya")
        return []
    return maya_refs.rig_status(scene)


# --------------------------------------------------------------------------- #
#  APPLY : dans mayapy
# --------------------------------------------------------------------------- #
def failed_edits(cmds, refnode):
    """Edits de reference EN ECHEC pour ce refnode. C'est LA mesure de l'anim perdue :
    un controleur renomme cote rig fait basculer ses edits ici, sans aucune erreur.
    /!\\ `failedEdits`/`successfulEdits` sont des MODIFICATEURS : ils doivent accompagner
    editStrings/editNodes/editAttrs, ils ne s'utilisent pas seuls (verifie en Maya 2025)."""
    try:
        return (
            cmds.referenceQuery(
                refnode, editStrings=True, failedEdits=True, successfulEdits=False
            )
            or []
        )
    except Exception as e:
        log("  referenceQuery(failedEdits) KO sur %s : %s" % (refnode, e))
        return []


DEFAULT_PRISM_APP = "C:/ILLOGIC_APP/Prism/2.0.18/app"
DEFAULT_PRISM_MAYA = "C:/ILLOGIC_APP/Prism/2.0.18/plugins/Maya/Integration/scripts"


def bootstrap_prism():
    """PrismCore initialise DANS mayapy. A appeler AVANT maya.standalone.initialize().

    /!\\ Deux contraintes, verifiees et non negociables :
      1. une QApplication doit exister AVANT l'init de Maya. Sinon PrismInit affiche
         "Cannot create Prism instance because no QApplication exists" et renvoie
         **None sans lever d'exception** -- un echec silencieux ;
      2. il faut poser `PrismInit.pcore` : les hooks studio (onSceneOpen...) lisent
         `PrismInit.pcore.appPlugin`, et plantent sans lui.
    En batch, PrismInit ajoute 'noUI' : les popups Prism sont LOGUES, jamais affiches
    (sinon un exec_() bloquerait le process pour toujours)."""
    try:
        from PySide6 import QtWidgets
    except ImportError:
        from PySide2 import QtWidgets
    if QtWidgets.QApplication.instance() is None:
        QtWidgets.QApplication(sys.argv)

    import maya.standalone

    maya.standalone.initialize(name="python")

    os.environ.setdefault("PRISM_ROOT", DEFAULT_PRISM_APP)
    integration = os.environ.get("PRISM_MAYA_INTEGRATION") or DEFAULT_PRISM_MAYA
    if integration not in sys.path:
        sys.path.append(integration)
    import PrismInit

    pcore = getattr(PrismInit, "pcore", None) or PrismInit.prismInit()
    if pcore is None:
        raise RuntimeError(
            "PrismInit a renvoye None (pas de QApplication ? PRISM_ROOT=%s)"
            % os.environ.get("PRISM_ROOT", "")
        )
    PrismInit.pcore = pcore  # les hooks studio le lisent
    return pcore


def ensure_project(pcore, project_cfg):
    """Charge le projet Prism. project_cfg DOIT etre le chemin du pipeline.json."""
    if not project_cfg or not os.path.isfile(project_cfg):
        raise RuntimeError(
            "--project doit etre le chemin du pipeline.json, pas '%s'" % project_cfg
        )
    if os.path.normpath(getattr(pcore, "prismIni", "") or "") != os.path.normpath(
        project_cfg
    ):
        pcore.changeProject(project_cfg)
    if not getattr(pcore, "prismIni", ""):
        raise RuntimeError("changeProject a echoue pour: %s" % project_cfg)
    log("Projet : %s  (%s)" % (getattr(pcore, "projectName", "?"), pcore.prismIni))


def prism_save(pcore, comment):
    """Version-up Prism de la scene ouverte. Retourne le nouveau chemin, ou None.

    On RELIT le chemin apres coup (`getCurrentFileName`) au lieu de faire confiance a la
    valeur de retour : c'est le fichier reellement ouvert qui fait foi."""
    before = (pcore.getCurrentFileName() or "").replace("\\", "/")
    pcore.saveScene(versionUp=True, comment=comment)
    after = (pcore.getCurrentFileName() or "").replace("\\", "/")
    if not after or after == before:
        log("saveScene n'a PAS produit de nouvelle version (toujours %s)" % after)
        return None
    if not os.path.isfile(after):
        log("saveScene annonce %s mais le fichier n'existe pas" % after)
        return None
    return after


def keep_published_usd_untouched(cmds):
    """Au save, les edits USD de la session vont DANS le .ma, jamais dans les fichiers USD.

    /!\\ Verifie en vrai : mayapy ne lit pas userPrefs.mel -> mayaUSD est a son defaut
    usine `mayaUsd_SerializedUsdEditsLocation = 1` ("save all edits back to usd files").
    Un version-up headless a ainsi RE-ECRIT le container publie
    SBX/testSplit/Export/USD/v005 (meme contenu, fins de ligne changees). Les artistes
    sont a 2 ("serialise dans le fichier Maya") : leurs saves ne touchent pas USD/v016
    de SH0125, date de publication intacte. On aligne le batch sur eux : 2 conserve les
    edits USD d'un artiste (restaures du .ma, re-serialises dans la nouvelle version),
    la ou 3 (ignorer) les perdrait."""
    key = "mayaUsd_SerializedUsdEditsLocation"
    prev = cmds.optionVar(q=key) if cmds.optionVar(exists=key) else None
    cmds.optionVar(iv=(key, 2))
    cmds.optionVar(iv=("mayaUsd_SerializedUsdEditsLocationPrompt", 0))
    log(
        "USD : edits serialises dans le .ma (optionVar %s -> 2), aucun USD reecrit"
        % prev
    )


def _same_file(a, b):
    def norm(p):
        return os.path.normcase(os.path.normpath((p or "").replace("//", "/")))

    return norm(a) == norm(b)


def open_scene(cmds, scene, res):
    """Ouvre la scene avec toutes ses references.

    /!\\ `cmds.file(open=True)` LEVE des qu'il y a eu des erreurs de lecture -- reference
    dont la version a ete supprimee du disque, attribut inconnu d'une autre version de
    mayaUSD... -- alors que la scene EST ouverte : c'est ce que la GUI affiche en warnings
    avant de laisser l'artiste travailler (vu sur SBX RoughLayout v035 : fishCute v001 et
    fishAncient v005 n'existent plus). On fait donc comme la GUI : si Maya a bien ouvert
    CETTE scene, on continue et on remonte les erreurs ; sinon on echoue."""
    log("Chargement de la scene dans Maya : %s" % scene)
    t0 = time.perf_counter()
    try:
        cmds.file(scene, open=True, force=True, prompt=False, loadReferenceDepth="all")
    except RuntimeError as e:
        if not _same_file(cmds.file(q=True, sceneName=True), scene):
            raise
        msgs = [m.strip() for m in str(e).splitlines() if m.strip()]
        res["warnings"].append(
            "scene ouverte avec des erreurs de lecture (comme en GUI) : "
            + " | ".join(msgs[:6])
        )
        log("  scene ouverte AVEC des erreurs de lecture (la GUI les affiche aussi) :")
        for m in msgs[:12]:
            log("    %s" % m)
    log("Scene chargee dans Maya (%.1fs)" % (time.perf_counter() - t0))


def swap_refs(cmds, item, targets, report):
    """Swappe toutes les references d'un asset vers `targets[ns] = chemin`.
    Mesure les edits en echec AVANT/APRES : c'est le seul signal fiable."""
    before = after = 0
    done = []
    for ref in item["refs"]:
        rn = ref.get("refnode")
        newp = targets.get(ref.get("ns"))
        if not rn or not newp:
            continue
        try:
            before += len(failed_edits(cmds, rn))
            cmds.file(newp, loadReference=rn)
            after += len(failed_edits(cmds, rn))
            done.append((ref.get("ns"), newp))
        except Exception as e:
            report["errors"].append("%s : %s" % (ref.get("ns") or rn, e))
            log("  ECHEC swap %s : %s" % (ref.get("ns") or rn, e))
    report["swapped"] += len(done)
    report["failed_before"] += before
    report["failed_after"] += after
    for ns, newp in done:
        log("  %-28s -> %s" % (ns, os.path.basename(newp)))
    # le detail PAR RIG dit a l'artiste lequel decocher (vu en vrai : hookSimple v002 ->
    # v005 perd 29 edits, sa hierarchie a change -> "foster parent")
    for r in report["rigs"]:
        if r["id"] == item["id"]:
            r["lost"] = after - before
    log(
        "  edits en echec pour ce rig : %d -> %d  (%+d)%s"
        % (before, after, after - before, "   <- ANIM PERDUE" if after > before else "")
    )
    return done


# --------------------------------------------------------------------------- #
#  EXPORTS : states du State Manager Prism
# --------------------------------------------------------------------------- #
def export_items(sm):
    """Items (QTreeWidgetItem) des states d'export du State Manager, ordre de la scene.
    On descend dans les Folders : un export range dans un dossier reste un export."""
    out = []

    def walk(item):
        ui = getattr(item, "ui", None)
        if getattr(ui, "className", "") in maya_refs.EXPORT_CLASSES:
            out.append(item)
        for i in range(item.childCount()):
            walk(item.child(i))

    tw = getattr(sm, "tw_export", None)
    for i in range(tw.topLevelItemCount() if tw is not None else 0):
        walk(tw.topLevelItem(i))
    return out


def _call(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _last_export(ui):
    props = _call(ui.getStateProps, {}) or {}
    last = props.get("lastexportpath") or ""
    return "" if last == "None" else last.replace("\\", "/")


def _state_manager(pcore):
    sm = _call(lambda: pcore.getStateManager(create=True))
    return sm if sm is not None and hasattr(sm, "publish") else None


# Plugins Prism studio qui ne font QUE de l'interface autour d'un publish : le
# pre_playblast_plugin (I:/<projet>/.pipelines_deploy/prism/plugins) regle les viewports,
# le HUD, l'overscan de la camera de vue et le burn-in des playblasts. En batch il n'y a
# aucun viewport : `cmds.getPanel(type="modelPanel")` renvoie None, son prePublish plante,
# et Prism ANNULE alors tout publish (vu en vrai, aucun export). On ne neutralise QUE
# lui : n'importe quel autre callback qui plante continue d'annuler, comme en GUI.
UI_ONLY_PLUGINS = ("pre_playblast_plugin",)
EXPORT_CALLBACKS = (
    "prePublish",
    "postPublish",
    "preExport",
    "postExport",
    "preMayaUSDExport",
)


# Ce que les fenetres modales ont "repondu" en batch (lu puis vide apres chaque export).
HEADLESS_DIALOGS = []


def install_headless_dialog_guard():
    """En batch, AUCUNE fenetre modale ne doit pouvoir bloquer : personne ne cliquera.

    Vu en vrai : le sanity_check studio (hook prePublish) ouvre `MainDialog.exec()` des
    qu'un check echoue -> mayapy gele indefiniment, CPU a zero. On remplace exec() par une
    reponse AUTOMATIQUE qui suit la regle de la GUI :
      - sanity_check avec une ERROR -> refuse : en GUI 'Publish anyways' est GRISE ;
      - sanity_check avec des WARNINGS seulement -> accepte : la GUI laisse publier ;
      - toute autre fenetre modale -> refusee (Cancel), et logue.
    Rien n'est contourne en silence : chaque reponse est loguee et remontee au verdict."""
    try:
        from PySide6 import QtWidgets
    except ImportError:
        from PySide2 import QtWidgets

    def _checks(dialog):
        out = []
        for c in getattr(dialog, "failed_check", None) or []:
            sev = getattr(getattr(c, "severity", None), "name", None) or str(
                getattr(c, "severity", "?")
            )
            msg = " ".join((getattr(c, "message", "") or "").split())
            out.append(
                {"label": getattr(c, "label", "?"), "severity": sev, "message": msg}
            )
        return out

    def _exec(self, *a, **k):
        title = _call(self.windowTitle, "") or type(self).__name__
        if hasattr(self, "failed_check"):  # le sanity_check studio
            checks = _checks(self)
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
            HEADLESS_DIALOGS.append(
                {"title": title, "sanity": checks, "accepted": bool(answer)}
            )
            return answer
        log("  fenetre modale '%s' refusee (batch : personne pour cliquer)" % title)
        HEADLESS_DIALOGS.append({"title": title, "accepted": False})
        return 0

    def _static_box(*a, **k):
        text = " | ".join(x for x in a if isinstance(x, str))  # titre | message
        log(
            "  QMessageBox statique refusee en batch : %s"
            % " ".join(text.split())[:300]
        )
        HEADLESS_DIALOGS.append(
            {"title": "QMessageBox", "text": text, "accepted": False}
        )
        return QtWidgets.QMessageBox.StandardButton.Cancel

    patched = []
    for cls in (QtWidgets.QDialog, QtWidgets.QMessageBox):
        for name in ("exec", "exec_"):
            if hasattr(cls, name):
                try:
                    setattr(cls, name, _exec)
                    patched.append("%s.%s" % (cls.__name__, name))
                except Exception as e:
                    log(
                        "  (garde-fou dialogues : %s.%s non patchable : %s)"
                        % (cls.__name__, name, e)
                    )
    for name in ("information", "warning", "critical", "question"):
        try:
            setattr(QtWidgets.QMessageBox, name, staticmethod(_static_box))
            patched.append("QMessageBox.%s" % name)
        except Exception as e:
            log(
                "  (garde-fou dialogues : QMessageBox.%s non patchable : %s)"
                % (name, e)
            )
    log(
        "garde-fou batch : aucune fenetre modale ne peut bloquer (%s)"
        % ", ".join(patched)
    )


def mute_ui_only_callbacks(pcore):
    """Retire, pour CE process seulement, les callbacks des plugins purement interface.
    Logue ce qui reste branche sur le chemin d'export (diagnostic)."""
    reg = getattr(getattr(pcore, "callbacks", None), "registeredCallbacks", None) or {}
    muted = []
    for name, entries in reg.items():
        for cb in list(entries):
            plugin = getattr(cb.get("plugin"), "pluginName", "") or ""
            if plugin in UI_ONLY_PLUGINS:
                entries.remove(cb)
                muted.append("%s.%s" % (plugin, name))
    if muted:
        log("callbacks interface neutralises en batch : %s" % ", ".join(sorted(muted)))
    for name in EXPORT_CALLBACKS:
        active = [
            "%s.%s"
            % (
                getattr(cb.get("plugin"), "pluginName", "") or "?",
                getattr(cb.get("function"), "__name__", "?"),
            )
            for cb in reg.get(name) or []
        ]
        if active:
            log("callbacks %s actifs : %s" % (name, ", ".join(active)))
    return muted


def run_exports(pcore, export_dir, uuids, comment, res, scene_saved):
    """Execute les states `uuids`, UN PAR UN, dans l'ordre de la scene -- comme un clic
    droit > Execute : publish(executeState=True) ne lance que le state donne, meme range
    dans un Folder (Folder.executeState filtre sur execStates).

    Un export n'est REUSSI que s'il a produit une NOUVELLE version sur disque. La valeur
    de retour de publish() ne suffit pas : False des qu'un hook a logue une erreur (meme
    si l'export est bien la), et rien n'empeche un state de "reussir" sans rien ecrire.

    /!\\ Un export .ma/.mb avec 'import references' RECHARGE la scene depuis le disque a la
    fin de son publish (Prism: reloadScenefile). Scene sauvee : on recharge la version
    qu'on vient d'ecrire, pas de souci. Scene NON sauvee : les swaps vivaient en memoire,
    ils sont perdus -> les exports suivants partiraient avec les ANCIENS rigs. On
    s'arrete alors, en le disant, plutot que de publier faux."""
    sm = _state_manager(pcore)
    if sm is None:
        res["errors"].append("State Manager Prism indisponible en headless")
        log("ERREUR: State Manager Prism indisponible -> aucun export.")
        return False
    mute_ui_only_callbacks(pcore)
    try:
        import sanity_check  # noqa: F401  (hook prePublish studio)

        log("hook prePublish : sanity_check importable -> il tournera")
    except Exception:
        log("hook prePublish : sanity_check non importable -> saute")

    by_uuid = {getattr(it.ui, "uuid", None): it for it in export_items(sm)}
    wanted = set(uuids)
    order = [u for u in by_uuid if u in wanted]
    all_ok = True
    for u in uuids:
        if u not in by_uuid:
            all_ok = False
            res["exports"].append(
                {"uuid": u, "ok": False, "error": "state introuvable dans la scene"}
            )
            log("ERREUR: state d'export %s introuvable dans le State Manager" % u)

    n = len(order)
    for i, uid in enumerate(order, 1):
        # items relus a chaque tour : si un export a recharge la scene, les anciens items
        # Qt peuvent etre detruits
        sm = _state_manager(pcore) or sm
        it = {getattr(x.ui, "uuid", None): x for x in export_items(sm)}.get(uid)
        entry = {"uuid": uid, "ok": False}
        res["exports"].append(entry)
        if it is None:
            entry["error"] = "state disparu du State Manager (scene rechargee ?)"
            log("ERREUR: %s" % entry["error"])
            all_ok = False
            continue
        ui = it.ui
        name = _call(lambda: it.text(0), uid) or uid
        product = _call(ui.getProductname, "") or ""
        entry.update({"name": name, "product": product})
        before_v = (
            preview.latest_product_version(export_dir, product)
            if export_dir and product
            else None
        )
        before_last = _last_export(ui)
        log("-" * 70)
        log(
            "Export Prism %d/%d : %s -> %s (derniere version publiee : %s)"
            % (i, n, name, product or "?", _vlabel(before_v) or "aucune")
        )
        print(">>>EXPORTPROGRESS>>>%d/%d<<<" % (i, n), flush=True)
        t0 = time.perf_counter()
        sm.reloadScenefile = False
        # le commentaire va AUSSI dans le champ du State Manager : c'est ce champ que lit
        # le sanity check studio (SizeCommentaire), pas l'argument de publish() -> vide
        # en batch, le check echouait a coup sur
        _call(lambda: sm.e_comment.setText(comment))
        del HEADLESS_DIALOGS[:]
        try:
            ret = sm.publish(
                executeState=True,
                states=[it],
                comment=comment,
                successPopup=False,
                saveScene=False,
                incrementScene=False,
                sanityChecks=True,  # en noUI : avertissements LOGUES, jamais bloquants
                versionWarning=False,
            )
        except Exception as e:
            ret = None
            entry["error"] = "publish a leve : %s" % e
        messages = []
        for r in getattr(sm, "publishResult", None) or []:
            rr = r.get("result") if isinstance(r, dict) else None
            if rr:
                messages.append(str(rr[0]))
        reloaded = bool(getattr(sm, "reloadScenefile", False))
        after_v = (
            preview.latest_product_version(export_dir, product)
            if export_dir and product
            else None
        )
        after_last = _last_export(ui) if not reloaded else ""
        moved = bool(
            after_last and after_last != before_last and os.path.exists(after_last)
        )
        grew = after_v is not None and (before_v is None or after_v > before_v)
        new_version = moved or grew
        if moved and not grew:
            # export publie HORS de l'entite de la scene : la version vient de son chemin
            after_v = preview.split_product(after_last)[2]
        errors = [m for m in messages if "error" in m.lower()]
        dialogs = list(HEADLESS_DIALOGS)
        sanity = [c for d in dialogs for c in d.get("sanity") or []]
        refused = [d for d in dialogs if not d.get("accepted")]
        if sanity:
            entry["sanity"] = sanity
        if refused and "error" not in entry:
            blocking = [c["label"] for c in sanity if c["severity"] == "ERROR"]
            entry["error"] = (
                "annule par le sanity check studio : %s" % "; ".join(blocking)
                if blocking
                else "annule : fenetre '%s' refusee en batch" % refused[0].get("title")
            )
        ok = new_version and not errors and "error" not in entry
        if new_version and not ok:
            # Prism cree le dossier vNNN AVANT que mayaUSD n'ecrive : un export qui plante
            # laisse une version CASSEE qui devient la "derniere" pour tout le monde (vu
            # en vrai : _layer_cam_camera/v004, un .usdc vide de 492 o). On le crie.
            broken = (
                os.path.dirname(after_last)
                if moved
                else os.path.join(export_dir, product, _vlabel(after_v) or "")
            )
            entry["broken_version"] = broken.replace("\\", "/")
            log(
                "  /!\\ %s %s a ete CREE mais l'export a ECHOUE : version cassee sur disque, "
                "a supprimer (sinon elle passe pour la derniere) : %s"
                % (product, _vlabel(after_v), entry["broken_version"])
            )
        entry.update(
            {
                "ok": ok,
                "from": _vlabel(before_v),
                "to": _vlabel(after_v) if ok else None,
                "path": after_last if moved else "",
                "messages": messages,
                "publish_returned": ret,
                "seconds": round(time.perf_counter() - t0, 1),
            }
        )
        if not ok and "error" not in entry:
            entry["error"] = errors[0] if errors else "aucune nouvelle version publiee"
        log(
            "  %s %s : %s -> %s  (%.1fs)%s"
            % (
                "OK  " if ok else "ECHEC",
                name,
                _vlabel(before_v) or "-",
                entry["to"] or "pas de nouvelle version",
                entry["seconds"],
                ("  | " + " / ".join(messages)) if messages else "",
            )
        )
        all_ok = all_ok and ok
        if reloaded:
            log("  (Prism a recharge la scene depuis le disque apres cet export)")
            if not scene_saved and i < n:
                msg = (
                    "'%s' a recharge la scene depuis le disque : la scene n'etant pas "
                    "sauvee, les exports suivants n'auraient PLUS la mise a jour des rigs "
                    "-> arret." % name
                )
                res["errors"].append(msg)
                log("ARRET: " + msg)
                for rest in order[i:]:
                    res["exports"].append(
                        {
                            "uuid": rest,
                            "ok": False,
                            "error": "non lance (scene rechargee)",
                        }
                    )
                return False
    return all_ok


# --------------------------------------------------------------------------- #
#  MAIN
# --------------------------------------------------------------------------- #
def emit_result(res):
    print("%s%s%s" % (RESULT_START, json.dumps(res), RESULT_END), flush=True)


def apply(args, scene, items, exports, res):
    """Le --apply complet. Retourne le code de sortie ; remplit `res` (le verdict)."""
    # --rigs ABSENT = tous les perimes (confort CLI) ; --rigs PRESENT, meme vide = exactement
    # ceux-la. Sinon "exports seuls" (--rigs sans valeur) mettrait a jour TOUS les rigs.
    if args.rigs is None:
        wanted = {it["id"] for it in items if it["stale"]}
    else:
        wanted = set(args.rigs)
    todo = [it for it in items if it["id"] in wanted and it["stale"]]
    want_exports = list(args.export or [])
    res["rigs"] = [
        {"id": it["id"], "from": it["version"], "to": it["latest"]} for it in todo
    ]

    if want_exports and args.save_as:
        log(
            "ERREUR: --export exige une scene DANS le pipeline (pas une copie --save-as)."
        )
        res["verdict"] = "bad_args"
        return 2
    if want_exports and not args.project:
        log("ERREUR: --export exige --project (les exports passent par Prism).")
        res["verdict"] = "bad_args"
        return 2
    known = {e["uuid"] for e in exports}
    unknown = [u for u in want_exports if u not in known]
    if unknown:
        log("ERREUR: state(s) d'export absent(s) de la scene : %s" % ", ".join(unknown))
        res["verdict"] = "bad_args"
        return 2
    if not todo and not want_exports:
        log("Rien a faire (aucun rig perime dans la selection, aucun export demande).")
        res["verdict"] = "nothing_to_do"
        return 0

    # cibles resolues AVANT d'ouvrir Maya : si un fichier cible manque, autant le savoir
    # tout de suite plutot qu'apres 3 minutes de chargement.
    plan = {}
    for it in todo:
        latest = int(it["latest"][1:])
        targets = {}
        for r in it["refs"]:
            ref = {
                "path": r["path"],
                "product": it["product"],
                "version": int(it["version"][1:]),
            }
            t = maya_refs.target_path(ref, latest)
            if not t:
                log("  ! cible introuvable pour %s (%s)" % (r["ns"], it["latest"]))
                res["warnings"].append(
                    "%s : %s introuvable sur disque" % (r["ns"], it["latest"])
                )
                continue
            targets[r["ns"]] = t
        if targets:
            plan[it["id"]] = targets
    if todo and not plan:
        log("Aucune cible resolue -> rien a faire.")
        res["verdict"] = "no_target"
        return 2

    # Prism d'abord (il initialise Maya au passage, dans le BON ordre : QApplication
    # avant maya.standalone). Sans --project, Maya nu : ni version-up ni export, mais
    # --save-as et --no-save restent utilisables.
    pcore = None
    if args.project:
        log("Demarrage de Prism dans Maya (~20 s)")
        pcore = bootstrap_prism()
        install_headless_dialog_guard()  # avant l'ouverture : les hooks peuvent popuper
        ensure_project(pcore, args.project.replace("\\", "/"))
    else:
        import maya.standalone

        maya.standalone.initialize(name="python")
    from maya import cmds

    open_scene(cmds, scene, res)
    # APRES l'ouverture (mayaUsdPlugin est charge par la scene et initialise ses
    # optionVars), AVANT toute sauvegarde (version-up, --save-as)
    keep_published_usd_untouched(cmds)

    for i, it in enumerate(todo, 1):
        print(">>>PROGRESS>>>%d/%d<<<" % (i, len(todo)), flush=True)
        if it["id"] not in plan:
            continue
        log("-" * 70)
        log(
            "Swap des rigs : %s  %s -> %s  (%d refs)"
            % (it["asset"], it["version"], it["latest"], it["n_refs"])
        )
        swap_refs(cmds, it, plan[it["id"]], res)

    if todo:
        lost = res["failed_after"] - res["failed_before"]
        res["lost"] = lost
        log("=" * 70)
        log(
            "Verification de l'animation : %d swap(s), edits en echec %d -> %d  (%+d)"
            % (res["swapped"], res["failed_before"], res["failed_after"], lost)
        )
        for e in res["errors"]:
            log("  ERREUR: %s" % e)
        if lost > 0 and not args.allow_lost_anim:
            losers = [
                "%s (%+d)" % (r["id"].split("|")[0], r["lost"])
                for r in res["rigs"]
                if (r.get("lost") or 0) > 0
            ]
            log(
                "REFUS d'incrementer et d'exporter : %d edit(s) de reference perdu(s) -> "
                "de l'animation a saute (%s). Verifie ces rigs a la main, ou relance sans "
                "eux (--allow-lost-anim pour passer outre)." % (lost, ", ".join(losers))
            )
            res["verdict"] = "refused_lost_anim"
            return 1
        if res["errors"] and not args.allow_lost_anim:
            log(
                "REFUS d'incrementer et d'exporter : des swaps ont echoue (voir ci-dessus)."
            )
            res["verdict"] = "refused_swap_errors"
            return 1

    comment = args.comment
    scene_saved = False
    if not todo:
        log("Aucun rig a mettre a jour : la scene ne change pas -> pas de version-up.")
        scene_saved = True  # le fichier sur disque EST la scene exportee
    elif args.save_as:
        out = args.save_as.replace("\\", "/")
        cmds.file(rename=out)
        cmds.file(save=True, type="mayaAscii", force=True)
        log("sauve en COPIE : %s" % out)
        print("%s%s%s" % (SAVED_START, out, SAVED_END), flush=True)
        res["saved"] = out
        res["verdict"] = "saved_copy"
        return 0
    elif args.no_save:
        log(
            "--no-save : scene NON sauvee (les swaps ne vivent que dans cette session)."
        )
        comment = args.comment + NOT_SAVED_SUFFIX
    else:
        if pcore is None:
            log("Pas de --project : version-up Prism impossible. Utilise --save-as.")
            res["verdict"] = "no_project"
            return 3
        log("Version-up de la scene (Prism)")
        newp = prism_save(pcore, args.comment)
        if not newp:
            log("ECHEC du version-up Prism -> rien n'a ete publie, aucun export lance.")
            res["verdict"] = "save_failed"
            return 1
        log("Scene version-upee : %s" % newp)
        print("%s%s%s" % (SAVED_START, newp, SAVED_END), flush=True)
        res["saved"] = newp
        scene_saved = True

    if not want_exports:
        res["verdict"] = "dry_run" if args.no_save else "ok"
        return 0

    log("=" * 70)
    log("Export Prism : %d state(s), commentaire '%s'" % (len(want_exports), comment))
    ok = run_exports(
        pcore,
        maya_refs.entity_export_dir(res.get("saved") or scene),
        want_exports,
        comment,
        res,
        scene_saved,
    )
    res["verdict"] = "ok" if ok else "export_failed"
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser(
        description="Met a jour les rigs perimes d'une scene d'anim Maya, puis exporte."
    )
    p.add_argument("--scene", required=True, help="chemin du .ma d'anim")
    p.add_argument("--project", default=None, help="pipeline.json Prism (save/exports)")
    p.add_argument(
        "--status", action="store_true", help="lister rigs + exports (sans Maya)"
    )
    p.add_argument("--apply", action="store_true", help="swapper les rigs choisis")
    p.add_argument(
        "--rigs",
        nargs="*",
        default=None,
        help="ids d'asset a mettre a jour (absent: TOUS les perimes ; sans valeur: aucun)",
    )
    p.add_argument(
        "--export",
        nargs="*",
        default=None,
        help="uuids des states d'export Prism a executer apres la mise a jour "
        "(defaut: aucun ; cf --status pour la liste)",
    )
    p.add_argument(
        "--no-save",
        action="store_true",
        help="ne pas sauver la scene (les exports partent quand meme, commentaire "
        "'(scene not saved)')",
    )
    p.add_argument(
        "--save-as",
        default=None,
        help="sauver en COPIE a ce chemin au lieu du version-up Prism (bac a sable)",
    )
    p.add_argument(
        "--comment",
        default="auto update - lop_update_cache",
        help="commentaire du version-up et des exports Prism",
    )
    p.add_argument(
        "--allow-lost-anim",
        action="store_true",
        help="incrementer MEME si des edits de reference sont perdus (deconseille)",
    )
    args = p.parse_args([a for a in sys.argv[1:] if a != "--"])

    scene = args.scene.replace("\\", "/")
    if not os.path.isfile(scene):
        log("ERREUR: scene introuvable: %s" % scene)
        sys.exit(2)
    log("=" * 70)
    log("Scene  : %s" % scene)
    log("Mode   : %s" % ("APPLY" if args.apply else "STATUS"))

    items = status(scene)
    exports = maya_refs.scene_exports(scene)
    stale = [it for it in items if it["stale"]]
    log(
        "Rigs   : %d asset(s), %d perime(s), %d reference(s)"
        % (len(items), len(stale), sum(i["n_refs"] for i in items))
    )
    for it in items:
        log(
            "  %-28s %-9s %s -> %s%s"
            % (
                it["asset"],
                it["product"],
                it["version"],
                it["latest"],
                ("   PERIME  (x%d refs)" % it["n_refs"]) if it["stale"] else "",
            )
            + (
                "   /!\\ version referencee ABSENTE du disque"
                if it.get("missing")
                else ""
            )
        )
    log("Exports: %d state(s)" % len(exports))
    for e in exports:
        log(
            "  %-24s %-22s %-6s %s  [%s]"
            % (
                e["name"],
                e["product"] or "?",
                e["latest"] or "-",
                "coche" if e["enabled"] else "decoche",
                e["uuid"],
            )
        )

    if not args.apply:
        print(STATUS_START)
        print(json.dumps(items, indent=2))
        print(STATUS_END)
        print(EXPORTS_START)
        print(json.dumps(exports, indent=2))
        print(EXPORTS_END, flush=True)
        sys.exit(0)

    res = {
        "scene": scene,
        "save_mode": "copy"
        if args.save_as
        else ("leave" if args.no_save else "version_up"),
        "rigs": [],
        "swapped": 0,
        "failed_before": 0,
        "failed_after": 0,
        "lost": 0,
        "errors": [],
        "warnings": [],
        "saved": None,
        "exports": [],
        "verdict": None,
    }
    try:
        code = apply(args, scene, items, exports, res)
    except Exception as e:  # une exception Python n'est pas un crash : on le DIT
        import traceback

        traceback.print_exc()
        res["errors"].append("%s: %s" % (type(e).__name__, e))
        res["verdict"] = res.get("verdict") or "exception"
        code = 1
    emit_result(res)
    sys.exit(code)


if __name__ == "__main__":
    main()
