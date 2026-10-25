# -*- coding: utf-8 -*-
"""
recache_cfx.py  -  Re-cache headless de shots cfx via hython + Prism 2.0.18

Ce script tourne DANS hython (pas de GUI Houdini). Pour un ou plusieurs shots
d'une scene .hip, il:
  1) bump le node d'import Prism (prism::LOP_Import::1.0) vers la DERNIERE version
  2) relance le cache (prism::lop_filecache::1.0) qui re-publie le layer cfx

Il ne SAUVE JAMAIS le .hip : les caches partent dans les product folders Prism,
donc plusieurs runs sur des shots differents n'entrent pas en conflit, et ta
scene reste intacte (ton fallback manuel est preserve).

--------------------------------------------------------------------------------
USAGE (via le .bat, ou directement) :

  hython recache_cfx.py --hip scene.hip --project .../pipeline.json --status --discover
  hython recache_cfx.py --hip scene.hip --project .../pipeline.json --shots sh010 --apply

  # (optionnel) --config <json> est encore accepte, surcharge ensuite par les flags.

Sans --apply => DRY-RUN : ne modifie/ecrit rien, se contente de diagnostiquer
(noms de parms reels, version courante vs latest, faisabilite du executeNode).
Avec --apply => execute reellement le bump + le re-cache.

  --all            traite tous les shots listes dans la config
  --shots A B C    traite ces shots precis
  --force          re-cache meme si deja a jour
--------------------------------------------------------------------------------
"""

import os
import re
import sys
import json
import time
import argparse

# preview = logique PURE PYTHON partagee avec l'UI (peremption par releve de cache).
# Le moteur tourne soit comme package, soit comme SCRIPT ISOLE (hython <path>/
# recache_cfx.py -> sys.path[0] = le dossier du module) : on couvre les deux.
try:
    from lop_update_cache import headless_guard, preview
except ImportError:  # pragma: no cover (depend du mode de lancement)
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import headless_guard
    import preview

# horloge relative au demarrage du process -> chaque ligne de log est horodatee (+Xs)
# pour voir d'un coup d'oeil quelle etape est longue (load scene / re-cache / submit).
_START = time.perf_counter()


# Fallback si PRISM_ROOT n'est pas deja dans l'env (hython lance "nu").
# ATTENTION: PRISM_ROOT pointe sur .../app (c'est la que vit Scripts/PrismCore.py).
DEFAULT_PRISM_APP = r"C:\ILLOGIC_APP\Prism\2.0.18\app"
DEFAULT_PRISM_INTEGRATION = r"C:\ILLOGIC_APP\Prism\2.0.18\plugins\Houdini\Integration"

# Valeurs par defaut de config (surchargees par --config puis par les flags CLI).
DEFAULTS = {
    "stage_root": "/stage",
    "import_node_pattern": "{shot}",
    "cache_node_pattern": "cache_{shot}",
    "import_node_type": "prism::LOP_Import",
    "cache_node_type": "prism::lop_filecache",
    "render_node_type": "prism::LOP_Render",
    "import_path_parm": "filepath",
    "tracked_layer": "_layer_anm_master",
    # commentaire de version-up : identifie l'OUTIL (sinon "auto update" seul est
    # ambigu -- on a deja vu une version lighting v258 "auto update" sans savoir qui).
    "save_comment": "auto update - lop_update_cache",
    "shots": [],
}


def _read_version():
    """Version = celle du package installe (importlib.metadata), sinon lue dans le
    pyproject.toml a la racine du repo (version geree par la CI du studio). Robuste
    que le moteur tourne comme package ou comme script isole via hython."""
    try:
        from importlib.metadata import version

        return version("lop_update_cache")
    except Exception:
        pass
    try:
        moddir = os.path.dirname(
            os.path.abspath(__file__)
        )  # <repo>/src/lop_update_cache
        root = os.path.dirname(os.path.dirname(moddir))  # <repo>
        with open(os.path.join(root, "pyproject.toml"), encoding="utf-8") as f:
            m = re.search(r'^\s*version\s*=\s*"([^"]+)"', f.read(), re.M)
            return m.group(1) if m else "dev"
    except Exception:
        return "dev"


VERSION = _read_version()


def log(msg):
    # flush pour que l'UI (QProcess) recoive les lignes en direct, pas par blocs.
    # prefixe [+Xs] = temps ecoule depuis le demarrage -> le saut entre 2 lignes = la
    # duree de l'etape entre elles (load scene / re-cache / submit).
    print("[recache_cfx] [%6.1fs] %s" % (time.perf_counter() - _START, msg), flush=True)


def _span(t0):
    """'78.5s [467.6s -> 546.1s]' : la duree ET la fenetre.

    Sans la fenetre, on lit l'horodatage de la ligne de FIN comme si c'etait le debut de
    l'operation (retour d'un user : '=> OK ... re-cache 78.5s' a 546.1s suivi du save a
    550.0s -> il a conclu que l'export avait pris 4s). La ligne dit maintenant d'ou a
    d'ou l'operation a tourne."""
    now = time.perf_counter()
    return "%.1fs [%.1fs -> %.1fs]" % (now - t0, t0 - _START, now - _START)


def prism_integration_versions(integration=None):
    """{(3, 11), (3, 10), ...} : versions de python pour lesquelles Prism fournit une
    integration Houdini (dossiers `python<X.Y>libs`). C'est ce qui decide si un Houdini
    donne est utilisable : Houdini 22.0.368 tourne en python 3.13, que Prism 2.0.18 ne
    fournit pas -> PrismInit ne peut pas se charger."""
    root = integration or DEFAULT_PRISM_INTEGRATION
    out = set()
    try:
        names = os.listdir(root)
    except Exception:
        return out
    for d in names:
        m = re.match(r"^python(\d+)\.(\d+)libs$", d)
        if m:
            out.add((int(m.group(1)), int(m.group(2))))
    return out


# --------------------------------------------------------------------------- #
#  Bootstrap Prism en headless
# --------------------------------------------------------------------------- #
def bootstrap_prism():
    """Retourne un PrismCore initialise (app='Houdini', noUI), projet non charge."""
    # 1) s'assurer que PrismInit (integration) est importable
    try:
        import PrismInit  # deja sur le path si hython lance via l'env studio
    except ImportError:
        # hython nu : on ajoute nous-memes le dossier d'integration correspondant
        # a la version de python de hython (Houdini 21 -> python3.11libs, etc.)
        want = sys.version_info[:2]
        avail = prism_integration_versions()
        cand = os.path.join(DEFAULT_PRISM_INTEGRATION, "python%d.%dlibs" % want)
        if want not in avail:
            # Prism ne fournit rien pour ce python -> le plus proche EN DESSOUS.
            # /!\ tri NUMERIQUE : un tri lexical rend 'python3.9libs' > 'python3.11libs'
            # et on chargeait alors l'integration 3.9 (PySide2) -> ModuleNotFoundError.
            below = [v for v in avail if v <= want]
            pick = max(below) if below else (max(avail) if avail else None)
            if pick is None:
                raise RuntimeError(
                    "Aucune integration Houdini dans %s" % DEFAULT_PRISM_INTEGRATION
                )
            log(
                "ATTENTION: Prism n'a pas d'integration pour python %d.%d "
                "(dispo: %s) -> essai avec python%d.%dlibs. Utilise un Houdini dont le "
                "python est supporte (ex 21.0.729 = python 3.11)."
                % (
                    want[0],
                    want[1],
                    ", ".join("%d.%d" % v for v in sorted(avail)),
                    pick[0],
                    pick[1],
                )
            )
            cand = os.path.join(DEFAULT_PRISM_INTEGRATION, "python%d.%dlibs" % pick)
        if cand not in sys.path:
            sys.path.append(cand)
        try:
            import PrismInit
        except Exception as e:
            raise RuntimeError(
                "Integration Prism illisible depuis %s : %s. "
                "hython tourne en python %d.%d ; Prism 2.0.18 fournit %s. "
                "Lance l'outil avec un Houdini dont le python est supporte "
                "(21.0.729 = python 3.11)."
                % (
                    cand,
                    e,
                    want[0],
                    want[1],
                    ", ".join("%d.%d" % v for v in sorted(avail)) or "rien",
                )
            )

    # 2) reutiliser le pcore global si pythonrc l'a deja cree ; sinon le creer
    pcore = getattr(PrismInit, "pcore", None)
    if pcore is None:
        os.environ.setdefault("PRISM_ROOT", DEFAULT_PRISM_APP)
        try:
            pcore = PrismInit.prismInit()
        except Exception as e:
            # message actionnable plutot qu'un traceback nu : la cause la plus courante
            # est un Houdini dont le python n'a pas d'integration Prism.
            raise RuntimeError(
                "PrismInit a echoue (%s: %s). hython tourne en python %d.%d ; "
                "Prism 2.0.18 fournit %s. Lance l'outil avec un Houdini supporte "
                "(21.0.729 = python 3.11)."
                % (
                    type(e).__name__,
                    e,
                    sys.version_info[0],
                    sys.version_info[1],
                    ", ".join("%d.%d" % v for v in sorted(prism_integration_versions()))
                    or "rien",
                )
            )

    if pcore is None:
        raise RuntimeError(
            "Impossible d'initialiser PrismCore. Verifie PRISM_ROOT (=%s) et que "
            "PySide6 est dispo dans hython." % os.environ.get("PRISM_ROOT", "")
        )
    return pcore


def ensure_project(pcore, project_cfg):
    """Charge le projet Prism (obligatoire en headless : pas de chargement auto).
    project_cfg DOIT etre le chemin du pipeline.json, PAS le nom du projet."""
    if not os.path.isfile(project_cfg):
        raise RuntimeError(
            "--project doit etre le chemin du pipeline.json "
            "(ex: I:/yuka_2604/00_Pipeline/pipeline.json), pas '%s'." % project_cfg
        )
    cur = os.path.normpath(getattr(pcore, "prismIni", "") or "")
    want = os.path.normpath(project_cfg)
    if cur != want:
        pcore.changeProject(project_cfg)
    loaded = getattr(pcore, "prismIni", "") or ""
    if not loaded:
        raise RuntimeError("changeProject a echoue pour: %s" % project_cfg)
    log("Projet : %s  (%s)" % (getattr(pcore, "projectName", "?"), loaded))


# --------------------------------------------------------------------------- #
#  Helpers Houdini
# --------------------------------------------------------------------------- #
def find_node(hou, stage_root, name, prefer_substr=None):
    """Cherche un node par nom exact sous stage_root (recursif). prefer_substr
    departage si plusieurs matches (ex: 'import', 'filecache')."""
    root = hou.node(stage_root)
    if root is None:
        return None, "stage_root introuvable: %s" % stage_root
    matches = [n for n in root.allSubChildren() if n.name() == name]
    if not matches:
        return None, "aucun node nomme '%s' sous %s" % (name, stage_root)
    if len(matches) > 1 and prefer_substr:
        pref = [n for n in matches if prefer_substr.lower() in n.type().name().lower()]
        if pref:
            matches = pref
    node = matches[0]
    warn = (
        "" if len(matches) == 1 else " (ATTENTION: %d nodes homonymes)" % len(matches)
    )
    return node, warn


def parm_val(node, name):
    p = node.parm(name)
    return None if p is None else p.eval()


def set_parm(node, name, value):
    p = node.parm(name)
    if p is None:
        return False
    p.set(value)
    return True


def inspect_node(hou, node, label):
    """Dump read-only de la structure d'un node : def HDA, enfants, boutons+callbacks,
    parms interessants. Sert a comprendre comment piloter un HDA inconnu."""
    log("=" * 70)
    log("INSPECT %s : %s  [%s]" % (label, node.path(), node.type().name()))
    d = node.type().definition()
    log("  HDA def : %s" % (d.libraryFilePath() if d else "(builtin, pas de HDA)"))

    kids = node.children()
    log("  enfants (%d) :" % len(kids))
    for c in kids:
        log("    - %-24s [%s]" % (c.name(), c.type().name()))

    keys = (
        "execute",
        "cache",
        "save",
        "write",
        "render",
        "cook",
        "version",
        "output",
        "file",
        "frame",
        "format",
        "load",
        "reload",
        "wedg",
        "publish",
    )
    log("  parms (boutons + interessants) :")
    for p in node.parms():
        pt = p.parmTemplate()
        is_btn = pt.type() == hou.parmTemplateType.Button
        nm = p.name().lower()
        if not (is_btn or any(k in nm for k in keys)):
            continue
        line = "    %-22s [%s]" % (p.name(), pt.type().name())
        if is_btn:
            cb = pt.scriptCallback() or ""
            lang = pt.scriptCallbackLanguage()
            line += "  callback(%s)= %s" % (lang, cb.replace("\n", " ")[:240])
        else:
            try:
                line += " = %r" % p.eval()
            except Exception:
                pass
        log(line)


# --------------------------------------------------------------------------- #
#  Detection par layer + traitement d'un item (cache apparie a son import)
# --------------------------------------------------------------------------- #
def tracked_layers(cfg):
    """Liste des layers suivis (toujours au moins un). Accepte l'ancienne forme
    `tracked_layer` (str) : les sidecars et les appels existants restent valides."""
    lst = [x for x in (cfg.get("tracked_layers") or []) if x]
    if not lst:
        one = cfg.get("tracked_layer")
        lst = [one] if one else []
    return lst or ["_layer_anm_master"]


def apply_tracked(st, tracked, mode):
    """Pose le verdict du shot (consumed/latest/stale/ignored/deciding) a partir de
    st['layers'], via preview.combine_layers -- MEME regle que l'UI.

    Un layer suivi que ce shot ne consomme pas est ignore ; si AUCUN ne l'est, on ne
    conclut pas (stale=None) et on dit pourquoi."""
    c = preview.combine_layers(st["layers"], tracked, mode)
    st["consumed"], st["latest"], st["stale"] = c["consumed"], c["latest"], c["stale"]
    st["ignored"], st["deciding"] = c["ignored"], c["deciding"]
    st["pinned"] = c["pinned"]  # suivis, epingles ET en retard (pas perimes)
    if not c["present"] and not st["err"]:
        have = ", ".join(sorted(st["layers"])) or "aucun"
        st["err"] = (
            "layer %s non consomme par cet import (contient: %s)" % (tracked[0], have)
            if len(tracked) == 1
            else "aucun des layers suivis (%s) n'est consomme par cet import "
            "(contient: %s)" % (", ".join(tracked), have)
        )
    return c


def compute_state(pcore, imp, cfg, shot=None):
    """Detection par LAYER, AGNOSTIQUE a ce que l'import pointe (cf stack_layers) :
      - import du CONTAINER du shot -> compare le TOKEN du layer tracke (defaut anim)
        fige dans le container consomme vs celui du dernier container dispo (PAS le
        numero du stack : immunise contre le re-bump container declenche par le cfx) ;
      - import DIRECT d'un layer master -> le produit EST le layer : on compare sa
        propre version consommee vs sa derniere version publiee.
    Si le layer tracke n'est pas consomme du tout par cet import -> err (l'UI affiche
    'n/a', PAS 'up to date' : la scene ne lit pas ce layer, il ne peut pas la perimer).
    Retourne un dict: cur, newp, consumed/latest (int version du layer),
    stack_consumed/stack_latest (str 'vNNN' du container USD), stale (bool|None), err."""
    path_parm = cfg.get("import_path_parm", "filepath")
    tracked_list = tracked_layers(cfg)
    tracked = tracked_list[0]  # nom unique, pour les messages et les replis
    mode = cfg.get("tracked_mode") or "or"
    st = {
        "cur": None,
        "newp": None,
        "consumed": None,
        "latest": None,
        "stack_consumed": None,
        "stack_latest": None,
        "stale": None,
        "layers": {},
        "ignored": [],  # layers suivis que CE shot ne consomme pas -> ignores
        "deciding": None,  # layer qui explique le verdict (le 1er perime)
        "err": "",
        "trust": "",  # verified / uncertain / none (fiabilite du releve de cache)
    }
    # --- 0) CE QUE L'IMPORT POINTE, et VERS QUOI le bumper -------------------------
    # /!\ `newp` (la cible du bump) doit etre resolu QUEL QUE SOIT le mode de detection.
    # Il etait calcule uniquement dans la branche historique : des qu'un releve existait,
    # compute_state sortait avant, newp restait None, et process_item loggait "import
    # deja au dernier shot USD" sans jamais bumper -> le shot restait a v061 alors que
    # v063 existait. Bug signale en prod (scene Confo).
    is_ls = imp is not None and is_layer_stack(imp)
    # lignes epinglees du usd_layer_stack : pas perimees meme en retard (cf mark_pins)
    st["pins"] = layer_stack_pins(imp) if is_ls else {}
    cur = (
        (layer_stack_resolved(imp) or [None])[0]
        if is_ls
        else (parm_val(imp, path_parm) if imp is not None else None)
    )
    st["cur"] = cur
    if cur and not is_ls:  # un layer_stack ne s'epingle pas : son bump est un `reload`
        try:
            latest = pcore.products.getLatestVersionFromPath(cur)
            st["newp"] = (
                pcore.products.getPreferredFileFromVersion(latest) if latest else None
            )
            st["stack_latest"] = (
                latest.get("version") if isinstance(latest, dict) else None
            )
        except Exception as e:
            st["err"] = "latest KO: %s" % e
        try:
            st["stack_consumed"] = pcore.products.getVersionFromFilepath(cur)
        except Exception:
            pass
        if not st["newp"]:
            # repli sur notre propre glob du produit : Prism rend parfois None
            # (constate sur SH0125/SH0140) et on se retrouverait sans cible de bump.
            p, v = preview.latest_product(cur)
            if p and v >= 0:
                st["newp"] = p

    # --- 1) RELEVE DE CACHE : source de verite, agnostique au type de node ---------
    # (cf preview.record_state). Indispensable pour usd_layer_stack, qui se resout
    # toujours au latest au chargement -> lui demander "que pointes-tu ?" dirait
    # toujours "a jour". Le releve dit avec quoi le cache PUBLIE a ete fait.
    rec = (cfg.get("cache_records") or {}).get(shot or "")
    node_layers = import_layers(imp) if imp is not None else {}
    if rec:
        export = preview.export_dir_of(cur)
        rs = preview.record_state(export, rec, tracked)
        st["trust"] = rs["trust"]
        # layers : le releve (consomme au cache) vs le disque (dernier publie)
        for name, v in (rec.get("layers") or {}).items():
            lv = preview.latest_product_version(export, name)
            st["layers"][name] = {
                "consumed": v,
                "latest": lv,
                "stale": bool(lv is not None and lv > v),
            }
        preview.mark_pins(st["layers"], st["pins"])
        c = apply_tracked(st, tracked_list, mode)
        if not c["present"] and len(tracked_list) == 1 and rs["err"]:
            st["err"] = rs["err"]  # message precis du releve ('absent du releve')
        if rs["trust"] == "uncertain" and rs["err"]:
            # la fiabilite du releve prime : on le DIT meme si le verdict tient
            st["err"] = " | ".join(x for x in (rs["err"], st["err"]) if x)
        return st

    # --- 2) usd_layer_stack SANS releve : on ne peut rien affirmer -----------------
    if is_ls:
        export = preview.export_dir_of(cur) if st["pins"] else None
        for name, v in node_layers.items():
            lv = v
            if export and preview.layer_dept(name) in st["pins"]:
                # epingle : le node ne dit pas le latest -> le disque, pour l'afficher
                lv = preview.latest_product_version(export, name)
                lv = v if lv is None else lv
            st["layers"][name] = {"consumed": v, "latest": lv, "stale": lv > v}
        preview.mark_pins(st["layers"], st["pins"])
        st["trust"] = "none"
        st["err"] = (
            "pas de releve pour ce shot : usd_layer_stack se resout toujours au dernier "
            "publish, la peremption ne peut PAS etre deduite de la scene. Lance un cache "
            "par l'outil pour initialiser le releve."
        )
        return st

    # --- 3) prism::LOP_Import : la version est EPINGLEE -> methode historique ------
    if not cur:
        st["err"] = st["err"] or "import/filepath absent"
        return st
    # tous les layers d'un coup (consomme vs latest)
    consumed_map = stack_layers(cur)
    latest_map = stack_layers(st["newp"] or cur)
    for name in set(consumed_map) | set(latest_map):
        c = consumed_map.get(name)
        lv = latest_map.get(name)
        st["layers"][name] = {
            "consumed": c,
            "latest": lv,
            # /!\ None (indecidable), PAS False : une version qu'on n'a pas su resoudre
            # ne veut pas dire "rien n'a bouge" -- ce serait un faux "a jour".
            "stale": (lv > c) if (c is not None and lv is not None) else None,
        }
    apply_tracked(st, tracked_list, mode)
    return st


def bump_import(pcore, imp, path_parm, newp):
    """Amene l'import a la DERNIERE version, quel que soit son type.

    - usd_layer_stack : il n'y a rien a epingler, il se resout tout seul au latest ->
      on presse `reload` (= hdaModule().update()) pour etre sur qu'il a vu les publishs
      arrives depuis le chargement de la scene.
    - prism::LOP_Import : bump PERSISTANT vers newp = set du parm de chemin PUIS
      setPathFromNode AVEC le contexte de changement de parm (parm + script_value) --
      indispensable, sinon le node re-resout et revient a l'ancienne version."""
    if is_layer_stack(imp):
        p = imp.parm("reload")
        if p is not None:
            p.pressButton()
            return
        try:  # pas de bouton -> on appelle l'update du HDA directement
            imp.hdaModule().update(imp)
        except Exception as e:
            log("  bump layer_stack KO (%s)" % e)
        return
    set_parm(imp, path_parm, newp)
    usd = pcore.getPlugin("USD")
    ui = getattr(getattr(usd, "api", None), "usdImport", None) if usd else None
    if ui is not None and hasattr(ui, "setPathFromNode"):
        try:
            ui.setPathFromNode(
                {"node": imp, "parm": imp.parm(path_parm), "script_value": newp}
            )
        except Exception:
            pass


def process_item(hou, pcore, item, cfg, apply_changes, force):
    """Diagnostic + (apply) bump import vers latest + re-cache. Ne sauve PAS la
    scene ici : le save du batch est fait une seule fois par main()."""
    cache = item["cache"]
    imp = item["import"]
    tracked = cfg.get("tracked_layer", "_layer_anm_master")
    rep = {
        "id": item["id"],
        "shot": item["shot"],
        "ok": False,
        "stale": None,
        "applied": False,
        "msg": "",
    }
    log("-" * 70)
    log(
        "ITEM %s  (shot %s, ancre=%s)"
        % (item["id"], item["shot"], item.get("anchor", "cache"))
    )
    caches = item.get("caches") or ([cache] if cache is not None else [])
    caches = select_caches(item, caches, cfg)
    if len(caches) > 1:
        log(
            "  caches : %d nodes -> %s"
            % (len(caches), ", ".join(c.name() for c in caches))
        )
        for c in caches:
            log("     %s  [%s]" % (c.path(), c.type().name()))
    elif cache is not None:
        log("  cache  : %s  [%s]" % (cache.path(), cache.type().name()))
    else:
        # scene de rendu sans filecache (ex Confo) : rien a re-cacher, on bumpe l'import
        # et on soumet le render
        log("  cache  : (aucun) -> bump import + render seulement")
    if imp is None:
        rep["msg"] = "import KO (topologie): %s" % item.get("warn", "")
        log("  import : INTROUVABLE par topologie (%s)" % item.get("warn", ""))
        return rep
    log("  import : %s  [%s]" % (imp.path(), imp.type().name()))

    st = compute_state(pcore, imp, cfg, shot=item.get("shot"))
    rep["stale"] = st["stale"]
    log("  filepath: %s" % st["cur"])
    # (champ Prism, souvent None -> on ne loggue que s'il dit quelque chose)
    if st["stack_consumed"] or st["stack_latest"]:
        log("  stack  : %s -> %s" % (st["stack_consumed"], st["stack_latest"]))
    log(
        "  %s : consommee=%s  latest=%s  -> %s"
        % (
            tracked,
            ("v%03d" % st["consumed"]) if st["consumed"] is not None else "?",
            ("v%03d" % st["latest"]) if st["latest"] is not None else "?",
            "PERIME" if st["stale"] else ("A JOUR" if st["stale"] is False else "N/A"),
        )
    )
    if st["err"]:
        log("  note   : %s" % st["err"])
    if st["cur"] is None:
        rep["msg"] = st["err"] or "etat indeterminable"
        return rep

    # chaine SOP a re-simuler (setups FX) : plan de l'UI, sinon toute la chaine
    sop_nodes = resolve_sop_plan(hou, item, cfg)
    is_fx = item.get("fx_sopcreate") is not None
    # Sim INATTEIGNABLE = on ne voit RIEN dans le reseau du sopcreate (cf fx_opaque).
    # /!\\ Surtout PAS "aucun cache SOP trouve" : un setup procedural ou un layer 'still'
    # n'a simplement rien a re-simuler, et se faisait refuser le re-cache a tort.
    locked = is_fx and bool(item.get("fx_opaque"))
    if sop_nodes:
        log(
            "  chaine SOP a re-simuler (%d): %s"
            % (len(sop_nodes), " -> ".join(n.name() for n in sop_nodes))
        )
    elif locked:
        log(
            "  setup FX : reseau de sim ILLISIBLE (HDA locked) -> impossible de "
            "re-simuler ici"
        )
    elif is_fx:
        log("  setup FX : aucun cache SOP a re-simuler -> republish seul")

    # --- DRY-RUN : on s'arrete la ---
    if not apply_changes:
        rep["ok"] = True
        rep["msg"] = "dry-run"
        return rep

    # FX perime + sim inatteignable : on NE bumpe PAS l'import et on NE republie PAS
    # -> sinon on masquerait la peremption (l'import passerait a jour sans re-sim).
    # Le shot reste marque perime ; re-sim manuel dans Houdini requis.
    if locked and (st["stale"] is True or force):
        rep["ok"] = True
        rep["skipped_locked"] = True
        rep["msg"] = (
            "sim inatteignable (HDA locked) -> re-sim manuel dans Houdini requis"
        )
        log(
            "  => SKIP (HDA locked) : import NON bumpe, pas de republish -> reste perime"
        )
        return rep

    if st["stale"] is not True and not force:
        rep["ok"] = True
        rep["msg"] = (
            "%s epingle (%s) : pas perime, depingler dans Houdini pour avancer"
            % (", ".join(st["pinned"]), _pins_text(st["pins"]))
            if st.get("pinned")
            else "pas de nouvelle %s (skip ; --force pour recacher quand meme)"
            % tracked
        )
        log("  => SKIP (%s)" % rep["msg"])
        return rep
    if st.get("pins"):
        # re-cache force sur un shot epingle : le pin est un choix de l'artiste, on ne
        # le retire pas -> le cache garde ces versions, on le dit
        log(
            "  pins du usd_layer_stack GARDES (%s) : le cache utilise ces versions"
            % _pins_text(st["pins"])
        )

    # --- APPLY : bump import -> (FX) re-sim chaine SOP dans l'ordre -> re-cache lop ---
    try:
        newp = st["newp"]
        if is_layer_stack(imp):
            # rien a epingler : on le force juste a re-resoudre (des publishs ont pu
            # arriver depuis le chargement de la scene)
            bump_import(pcore, imp, cfg.get("import_path_parm", "filepath"), None)
            pins = layer_stack_pins(imp)
            log(
                "  layer_stack : reload -> %s%s"
                % (
                    ", ".join(
                        "%s v%03d" % (k, v)
                        for k, v in sorted(import_layers(imp).items())
                    ),
                    ("  (epingles, gardes : %s)" % _pins_text(pins)) if pins else "",
                )
            )
        elif newp and newp != st["cur"]:
            bump_import(pcore, imp, cfg.get("import_path_parm", "filepath"), newp)
            log("  bump import -> %s" % newp)
        else:
            log("  import deja au dernier shot USD")
        # re-simuler les caches SOP dans l'ordre (avec le nouvel anim en amont)
        for i, sc in enumerate(sop_nodes):
            log(
                "  [%d/%d] re-cache SOP %s [%s] ..."
                % (i + 1, len(sop_nodes), sc.name(), sc.type().name())
            )
            print(
                ">>>SUBPROGRESS>>>%d/%d<<<SUBPROGRESS<<<" % (i + 1, len(sop_nodes)),
                flush=True,
            )
            execute_sop_cache(sc)
            serrs = node_errors(sc)
            if serrs:
                rep["msg"] = "SOP %s erreurs: %s" % (sc.name(), " | ".join(serrs))
                log("  => ECHEC SOP: %s" % rep["msg"])
                return rep
        if not caches:
            # scene de rendu SANS filecache : le livrable est le render, l'import bumpe
            # suffit. Le submit se fait dans la 2e passe (apres le save).
            rep["ok"] = True
            rep["applied"] = True
            rep["msg"] = "import bumpe (pas de cache dans cette scene)"
            log("  => OK (pas de cache a executer)")
            rep["record"] = build_cache_record(imp, None, pcore)
            return rep
        # un shot peut avoir PLUSIEURS filecache (produits differents) -> tous, dans
        # l'ordre. Un echec sur l'un arrete l'item : pas de version-up sur un livrable
        # incomplet.
        results = []
        for i, c in enumerate(caches):
            log(
                "  [%d/%d] execute lop_filecache %s ..."
                % (i + 1, len(caches), c.name())
            )
            _t = time.perf_counter()
            n_dialogs = len(headless_guard.DIALOGS)
            res = execute_cache(pcore, c)
            span = _span(_t)
            errs = node_errors(c)
            # un sanity check studio refuse (hook prePublish) annule le publish SANS
            # erreur sur le node : sans ce test, un cache non ecrit passait pour OK
            errs += [
                headless_guard.describe(d)
                for d in headless_guard.refused_since(n_dialogs)
            ]
            if errs:
                rep["msg"] = "publish KO (%s): %s" % (c.name(), " | ".join(errs))
                log("  => ECHEC publish: %s" % rep["msg"])
                return rep  # applied reste False -> pas de version-up sur echec
            log("  => OK (%s, re-cache %s)" % (res, span))
            results.append(res)
        rep["ok"] = True
        rep["applied"] = True
        rep["msg"] = "re-cache OK (%d SOP + %d lop ; %s)" % (
            len(sop_nodes),
            len(caches),
            " | ".join(results),
        )
        # RELEVE : ce que ce cache a REELLEMENT consomme + ce qu'il a publie.
        # C'est la source de verite de la peremption (independante du type de node,
        # cf preview.record_state). Renvoye a l'UI, qui l'ecrit dans le sidecar.
        rep["record"] = build_cache_record(imp, caches, pcore)
        if rep["record"]:
            log(
                "  releve : %s -> publie %s"
                % (
                    ", ".join(
                        "%s v%03d" % (k, v)
                        for k, v in sorted((rep["record"].get("layers") or {}).items())
                    )
                    or "(aucun layer)",
                    ", ".join(
                        "%s v%03d" % (k, v or 0)
                        for k, v in sorted(
                            (rep["record"].get("products") or {}).items()
                        )
                    )
                    or "(aucun produit)",
                )
            )
    except Exception as e:
        import traceback

        rep["msg"] = "EXCEPTION: %s" % e
        log("  => EXCEPTION:\n%s" % traceback.format_exc())
    return rep


def cache_output(pcore, cache):
    """(produit, version) REELLEMENT publies par un lop_filecache, lus sur son CHEMIN
    DE SORTIE resolu (`usdExport ... getOutputName()`), pas sur un parm.

    /!\\ Le parm `department` ne suffit PAS : sur frederic_2603, deux caches affichent
    tous les deux department='fx' (donc '_layer_fx_master' par deduction) alors qu'ils
    publient en realite `_layer_fx_snow_still` et `_layer_fx_snow_sim`. Deduire le
    produit du departement ecrivait donc un produit INEXISTANT dans le releve, ce qui
    neutralisait silencieusement le garde-fou "cache refait hors outil".
    (None, None) si Prism ne resout pas -- l'appelant retombe sur le departement."""
    if cache is None or pcore is None:
        return None, None
    try:
        usd = pcore.getPlugin("USD")
        ue = getattr(getattr(usd, "api", None), "usdExport", None)
        st = ue.getStateFromNode({"node": cache}) if ue else None
        out = st.ui.getOutputName() if st is not None else None
    except Exception:
        return None, None
    path = out[0] if isinstance(out, (tuple, list)) and out else out
    if not isinstance(path, str) or not path:
        return None, None
    _root, name, ver = preview.split_product(path)
    return (name, ver) if name and ver >= 0 else (None, None)


def cache_product(cache, pcore=None):
    """Produit publie par un lop_filecache. Chemin de sortie resolu d'abord (verite),
    sinon deduction '_layer_<department>_master'.

    /!\\ `department` est un parm MENU : eval() rend l'INDEX (5), pas le texte -- on
    ecrivait '_layer_5_master' dans les releves (vu en vrai dans un sidecar), ce qui
    tuait silencieusement le garde-fou "cache hors outil". Il faut evalAsString().
    `backupDepartment` (chaine simple) sert de repli, et on REFUSE une valeur numerique
    plutot que de fabriquer un nom de produit faux."""
    prod, _ = cache_output(pcore, cache)
    if prod:
        return prod
    for pname in ("department", "backupDepartment"):
        p = cache.parm(pname) if cache is not None else None
        if p is None:
            continue
        try:
            val = p.evalAsString()
        except Exception:
            val = p.eval()
        val = str(val or "").strip()
        if val and not val.isdigit():
            return "_layer_%s_master" % val
    return None


def build_cache_record(imp, caches, pcore=None):
    """Releve des caches qui viennent de reussir : ce qu'ils ont CONSOMME et ce qu'ils
    ont PUBLIE. C'est ce releve (et pas l'etat de la scene) qui dira plus tard si le
    shot est perime -- indispensable avec usd_layer_stack, qui se resout toujours au
    latest. Les versions des produits publies reperent un cache refait HORS outil.

    `caches` : un node, une liste de nodes, ou None. Un shot peut avoir PLUSIEURS
    filecache (vu sur frederic_2603 : _layer_fx_snow_still ET _layer_fx_snow_sim) ->
    on releve TOUS les produits (`products`), pas seulement le premier. `product` /
    `product_version` restent ecrits (le 1er) : un sidecar ecrit par cette version
    reste lisible par une version anterieure de l'outil."""
    if imp is None:
        return None
    if caches is None:
        caches = []
    elif not isinstance(caches, (list, tuple)):
        caches = [caches]
    layers = import_layers(imp)
    src = (
        (layer_stack_resolved(imp) or [None])[0]
        if is_layer_stack(imp)
        else parm_val(imp, "filepath")
    )
    export = preview.export_dir_of(src)
    products = {}
    for c in caches:
        name, ver = cache_output(pcore, c)
        if not name:
            name = cache_product(c, pcore)
            ver = (
                preview.latest_product_version(export, name)
                if (export and name)
                else None
            )
        if name:
            products[name] = ver
    first = next(iter(products), None)
    return {
        "layers": layers,
        "products": products,
        "product": first,
        "product_version": products.get(first),
        "export": export,
        "at": time.time(),
    }


def select_caches(item, caches, cfg):
    """Filtre les caches d'un item par le plan de l'UI (cfg['cache_plan']).

    /!\\ Une entree ABSENTE veut dire "tous" (appel direct en ligne de commande, ou
    ancienne UI) ; une liste VIDE veut dire "aucun" (l'artiste a tout decoche : on bumpe
    l'import et on rend, sans recacher). Confondre les deux ferait cacher ce qu'il a
    explicitement exclu."""
    plan = cfg.get("cache_plan") or {}
    if item.get("id") not in plan:
        return caches
    keep = set(plan.get(item["id"]) or [])
    return [c for c in caches if c.path() in keep]


def harvest_records(items, reports, cfg):
    """Releves des shots qui viennent d'etre caches : {shot: record}. Les injecte AUSSI
    dans cfg["cache_records"], sinon le rafraichissement de fin de run rejuge le shot
    avec le releve d'AVANT le cache et le declare PERIME -- la ligne restait rouge
    jusqu'a ce que l'utilisateur clique Reload (bug signale en prod)."""
    recs = {}
    for it, r in zip(items, reports):
        if r.get("record") and r.get("applied"):
            recs[it["shot"]] = r["record"]
    if recs:
        cfg.setdefault("cache_records", {}).update(recs)
    return recs


def execute_cache(pcore, node):
    """Lance l'ecriture du cache selon le type de node. Neutralise d'abord tout
    ce qui sauverait la scene / bloquerait en headless (on ne sauve JAMAIS le hip)."""
    # garde-fous communs (guardes: set seulement si le parm existe)
    for pn, val in (
        ("saveScene", 0),
        ("incrementScene", 0),
        ("sanityChecks", 0),
        ("showSuccessPopup", 0),
        ("background", 0),
    ):
        set_parm(node, pn, val)

    tname = node.type().name().lower()
    if "lop_filecache" in tname:
        # LOP filecache = HDA du plugin USD : bouton execute -> usdExport.executePressed
        usd = pcore.getPlugin("USD")
        ue = getattr(getattr(usd, "api", None), "usdExport", None) if usd else None
        if ue is not None and hasattr(ue, "executePressed"):
            ue.executePressed({"node": node})
            return "usdExport.executePressed"
        p = node.parm("execute")
        if p is None:
            raise RuntimeError(
                "LOP filecache: ni USD api ni bouton 'execute' sur %s" % node.path()
            )
        p.pressButton()
        return "pressButton(execute)"

    # SOP filecache stock (prism::Filecache)
    fc = pcore.appPlugin.filecache
    set_parm(node, "useWedging", 0)  # wedging = PDG, incompatible headless
    set_parm(node, "nextVersionWrite", 1)  # auto-increment de version
    return fc.executeNode(node)


def node_errors(node):
    """Erreurs du node ET de ses descendants (recursif). Un HDA de cache (LOP filecache,
    prism::Filecache) porte souvent l'erreur reelle sur un ROP/rop_usd INTERNE, pas sur
    le node de tete -> node.errors() seul rate 'No frame range is set on the source
    stage' & co. On ratisse donc tout le sous-reseau."""
    errs = []
    try:
        errs.extend(node.errors())
    except Exception:
        pass
    try:
        for ch in node.allSubChildren():
            try:
                e = ch.errors()
                if e:
                    errs.extend(e)
            except Exception:
                pass
    except Exception:
        pass
    return errs


def execute_sop_cache(node):
    """Re-ecrit un cache SOP en pressant son bouton 'execute' (Save to Disk). On presse
    le bouton du node lui-meme -> reproduit FIDELEMENT l'action manuelle de l'artiste
    (respecte range / substeps / version / sim configures sur le node). Neutralise
    d'abord ce qui sauverait la scene ou bloquerait en headless (cas Prism)."""
    for pn, val in (
        ("saveScene", 0),
        ("incrementScene", 0),
        ("sanityChecks", 0),
        ("showSuccessPopup", 0),
        ("background", 0),
        ("useWedging", 0),
    ):
        set_parm(node, pn, val)
    p = node.parm("execute")
    if p is None:
        raise RuntimeError(
            "pas de bouton 'execute' sur %s [%s]" % (node.path(), node.type().name())
        )
    p.pressButton()
    return "pressButton(execute)"


def resolve_sop_plan(hou, item, cfg):
    """Nodes SOP a re-executer pour cet item, DANS L'ORDRE. Depuis le plan de l'UI
    (cfg['fx_plan'][cache_id] = [paths coches, ordonnes]) si fourni, sinon TOUTE la
    chaine decouverte (ordre topologique). Une entree [] = l'artiste a tout decoche
    -> pas de re-sim (republish du lop_filecache seul)."""
    plan = (cfg.get("fx_plan") or {}).get(item["id"])
    if plan is None:
        return list(item.get("fx_chain") or [])  # defaut : toute la chaine
    nodes = []
    for p in plan:
        n = hou.node(p)
        if n is not None:
            nodes.append(n)
    return nodes


_SUBLAYER_RE = re.compile(r"([^/@]+)/v(\d+)/")  # .../_layer_x_master/v010/...
_PRODUCT_RE = re.compile(r"([^/\\]+)[/\\]v(\d+)[/\\][^/\\]+$")


def product_layers(usd_path):
    """{produit: version} du produit Prism que `usd_path` DESIGNE lui-meme
    (.../Export/<produit>/vNNN/<fichier>). Ex .../_layer_anm_master/v012/x.usda
    -> {'_layer_anm_master': 12}. {} si le chemin n'a pas cette forme."""
    m = _PRODUCT_RE.search((usd_path or "").replace("\\", "/"))
    return {m.group(1): int(m.group(2))} if m else {}


def stack_layers(usd_path):
    """{nom_layer: version_int} de TOUT ce que consomme `usd_path` :
      - ses subLayers versionnes (le stack) ;
      - ET le produit de `usd_path` LUI-MEME, a sa propre version.

    Ce 2e point rend la detection AGNOSTIQUE a la granularite de l'import : que la
    scene importe le container du shot (-> '_layer_anm_master' sort des subLayers) ou
    directement .../_layer_anm_master/v012/... (-> il sort du chemin), le layer tracke
    est trouve dans les deux cas. Le produit propre PRIME : c'est la version reellement
    consommee, pas une mention interne.

    /!\\ Un _layer_x_master n'est PAS une feuille : il sublayer ses _layer_x_class /
    _layer_x_main (verifie sur yuka_2604). D'ou la fusion plutot qu'un fallback
    'pas de subLayers -> c'est le produit', qui ne se declencherait jamais.
    Parser tout d'un coup permet a l'UI de changer de layer tracke sans recharger."""
    if not usd_path:
        return {}
    out = {}
    try:
        from pxr import Sdf

        layer = Sdf.Layer.FindOrOpen(usd_path)
        for sub in layer.subLayerPaths if layer is not None else []:
            # les subLayers peuvent etre relatifs OU absolus Windows (backslashes)
            m = _SUBLAYER_RE.search(str(sub).replace("\\", "/"))
            if m:
                name, v = m.group(1), int(m.group(2))
                if name not in out or v > out[name]:
                    out[name] = v
    except Exception:
        pass
    out.update(product_layers(usd_path))
    return out


def upstream_import(hou, node, cfg, cap=20000):
    """Remonte inputs() depuis un node de cache jusqu'aux imports ATTEIGNABLES (les deux
    generations : prism::LOP_Import ET illogic::usd_layer_stack).

    C'est le signal le plus sur : seul l'import REELLEMENT CABLE au filecache alimente
    ce cache. Les autres imports de la scene (residus, autres shots, doublons) ne le
    concernent pas, meme s'ils portent le meme shot.

    NOTE: sur les setups FX (caches SOP figes en amont), la chaine LOP ne relie PAS le
    cache a son import -> renvoie [] ; on retombe alors sur l'appariement par shot."""
    imp_type = cfg.get("import_node_type", "prism::LOP_Import").lower()
    seen = set()
    found = {}
    stack = [x for x in node.inputs() if x is not None]
    steps = 0
    while stack and steps < cap:
        steps += 1
        n = stack.pop()
        p = n.path()
        if p in seen:
            continue
        seen.add(p)
        tn = n.type().name().lower()
        if imp_type in tn or "lop_import" in tn or is_layer_stack(n):
            found[p] = n
            continue  # on ne remonte pas au-dela d'un import
        stack.extend([x for x in n.inputs() if x is not None])
    return list(found.values())


# --------------------------------------------------------------------------- #
#  Deux generations de node d'import cohabitent dans les scenes :
#
#   - prism::LOP_Import::1.0        (Prism) : un `filepath` EPINGLE sur une version
#     precise (container du shot, ou produit d'un layer master).
#   - illogic::usd_layer_stack::1.0 (HDA maison, remplace le precedent : plus rapide) :
#     shot explicite (`sequence`/`shot`), multiparm `department#`/`version#`, et un parm
#     `resolved` (chemins resolus, 1 par ligne).
#     /!\ Son OnLoaded appelle rescan() -> update() : il se resout vers la derniere
#     version publiee au chargement de la scene, et `version#` est une LECTURE (update()
#     y ecrit le resultat), pas un reglage. Donc "bumper" = presser `reload` (= rescan),
#     et comparer "ce que l'import pointe" vs "le latest" ne veut plus rien dire apres
#     un load : c'est toujours egal. La peremption se lit ailleurs (cf le releve fait au
#     moment du cache).
#     /!\ SAUF les lignes EPINGLEES (2.1+, parm `pin#` = 'vNNN' au lieu de 'latest') :
#     rescan les laisse sur leur version (verifie dans le PythonModule de la 2.2 en
#     prod). Un layer epingle en retard n'est pas perime pour l'outil (choix de
#     l'artiste, cf preview.mark_pins) et l'outil ne depingle JAMAIS.
# --------------------------------------------------------------------------- #
LAYER_STACK_TYPE = "illogic::usd_layer_stack"


def is_layer_stack(node):
    return LAYER_STACK_TYPE in node.type().name().lower()


def layer_stack_shot(node):
    """Entite d'un usd_layer_stack, depuis ses parms : 'SEQ/SHOT' en mode shot, le NOM
    DE L'ASSET en mode asset.

    Le nom d'asset nu est ce que renvoie deja `shot_from_cache_output` (repli
    `ent.get('asset')` de Prism) -> les deux sources s'accordent, l'appariement par
    entite et les releves marchent pareil des deux cotes. /!\\ Ne pas confondre avec la
    scene RANGEE sous /Assets : elle, peut tres bien porter des entites 'shot'."""
    if (parm_val(node, "mode") or "shot") != "shot":
        return (parm_val(node, "asset") or "").strip() or None
    seq = (parm_val(node, "sequence") or "").strip()
    shot = (parm_val(node, "shot") or "").strip()
    return ("%s/%s" % (seq, shot)) if seq and shot else None


def layer_stack_pins(node):
    """{departement: pin} des lignes ACTIVES figees du usd_layer_stack. {} pour un node
    sans pins (1.0, 2.0) ou si tout suit 'latest'. Une ligne decochee ne charge rien :
    son pin ne compte pas.
      - 2.1+ : pin de LIGNE (`pin#` = 'vNNN') -> 'vNNN' ;
      - 2.5+ : `shotversion` = 'vNNN' fige TOUTES les lignes sans pin propre sur les
        versions du container Export/USD/vNNN du shot -> 'shot vNNN'. Le pin de ligne
        reste prioritaire (comme dans le HDA, `_row_version`)."""
    if node is None or not is_layer_stack(node):
        return {}
    shotver = (parm_val(node, "shotversion") or "").strip()
    shotver = "" if shotver in ("", "latest") else shotver
    out = {}
    cnt = parm_val(node, "sublayers") or 0
    for i in range(1, int(cnt) + 1):
        dept = (parm_val(node, "department%d" % i) or "").strip().lower()
        if not dept or not parm_val(node, "enable%d" % i):
            continue
        pin = (parm_val(node, "pin%d" % i) or "").strip()  # None : HDA sans pin#
        if pin and pin != "latest":
            out[dept] = pin
        elif shotver:
            out[dept] = "shot %s" % shotver
    return out


def _pins_text(pins):
    return ", ".join("%s %s" % (d, v) for d, v in sorted((pins or {}).items()))


def layer_stack_resolved(node):
    """Chemins USD reellement resolus par le node (parm `resolved`, 1 par ligne)."""
    raw = parm_val(node, "resolved") or ""
    return [p.strip().replace("\\", "/") for p in raw.splitlines() if p.strip()]


def layer_stack_layers(node):
    """{produit: version} de ce que le node charge, lu sur les chemins RESOLUS (source
    de verite ; `department#`/`version#` n'en sont que le reflet)."""
    out = {}
    for p in layer_stack_resolved(node):
        out.update(product_layers(p))
    if out:
        return out
    # repli : le multiparm, si `resolved` est vide (node jamais update)
    cnt = parm_val(node, "sublayers") or 0
    for i in range(1, int(cnt) + 1):
        dept = (parm_val(node, "department%d" % i) or "").strip()
        ver = (parm_val(node, "version%d" % i) or "").strip()
        m = re.match(r"^v(\d+)$", ver)
        if dept and m:
            out["_layer_%s_master" % dept] = int(m.group(1))
    return out


def import_layers(node):
    """{produit: version} consommes par un node d'import, quel que soit son type."""
    if is_layer_stack(node):
        return layer_stack_layers(node)
    fp = parm_val(node, "filepath")
    return stack_layers(fp) if fp else {}


def collect_imports(hou, pcore, cfg):
    """Tous les nodes d'import de la scene (Prism ET usd_layer_stack), avec le SHOT
    qu'ils importent (lu du CONTENU/des parms, jamais du nom du node) et les layers
    qu'ils chargent. Sert a apparier un cache a SON import PAR CONTENU quand la
    topologie ne les relie pas (setups FX)."""
    stage_root = cfg.get("stage_root", "/stage")
    imp_type = cfg.get("import_node_type", "prism::LOP_Import").lower()
    path_parm = cfg.get("import_path_parm", "filepath")
    root = hou.node(stage_root)
    out = []
    if root is None:
        return out
    for n in root.allSubChildren():
        tn = n.type().name().lower()
        if is_layer_stack(n):
            shot = layer_stack_shot(n)
            res = layer_stack_resolved(n)
            out.append(
                {
                    "node": n,
                    "shot": shot or "?",
                    "fp": res[0] if res else None,
                    "layers": layer_stack_layers(n),
                }
            )
            continue
        if not (imp_type in tn or "lop_import" in tn):
            continue
        fp = parm_val(n, path_parm)
        out.append(
            {
                "node": n,
                "shot": shot_label(pcore, n, cfg),
                "fp": fp,
                "layers": stack_layers(fp) if fp else {},
            }
        )
    return out


def _import_has_layer(info, tracked):
    lm = info.get("layers") or {}
    if tracked in lm:
        return True
    return any(tracked in k or k in tracked for k in lm)


def import_for_shot(imports, shot, tracked, exported=None):
    """Retrouve l'import qui importe `shot` (appariement PAR CONTENU, sans nom ni cablage).
    Departage, dans l'ordre :
      1) les imports REELLEMENT en amont d'un export de la scene (`exported`) -- sur une
         scene FX, 76 des 77 imports sont des cameras qui n'alimentent rien : les garder
         comme candidats, c'est risquer d'apparier le cache a une camera ;
      2) puis celui qui porte le layer tracke (l'import qui a l'anim, pas un doublon).
    Retourne (node|None, ambiguous_bool)."""
    if not shot or shot == "?":
        return None, False
    cands = [im for im in imports if im["shot"] == shot]
    if not cands:
        return None, False
    if exported:
        used = [im for im in cands if im["node"].path() in exported]
        cands = used or cands  # aucun cable -> on garde tout plutot que rien
    if len(cands) == 1:
        return cands[0]["node"], False
    withlayer = [im for im in cands if _import_has_layer(im, tracked)]
    if len(withlayer) == 1:
        return withlayer[0]["node"], False
    if withlayer:
        return withlayer[0]["node"], True  # plusieurs avec le layer -> 1er, ambigu
    return cands[0]["node"], True  # aucun avec le layer -> 1er candidat, ambigu


# --------------------------------------------------------------------------- #
#  FX : chaine de caches SOP a re-executer pour re-simuler
#
#  Sur un setup FX (seaweed & co), le lop_filecache USD relit des bgeo SOP FIGES
#  (loadfromdisk=1) : le bumper/re-executer seul REPUBLIE l'ancienne sim. Pour
#  vraiment re-simuler, il faut re-executer les filecaches SOP en amont, dans
#  l'ordre (detangle -> sim -> ...), PUIS le lop_filecache.
#
#  On reste GENERIQUE (pas de lecture de HDA specifique) : on remonte jusqu'au
#  sopcreate, on enumere les filecaches SOP disque atteignables, on les ordonne
#  par dependance ; l'UI en fait une liste cochable (l'artiste decide lesquels).
#  Limite : un HDA sim LOCKED cache ses caches internes -> chaine vide (on ne
#  peut alors que republier le lop_filecache).
# --------------------------------------------------------------------------- #
FX_SOP_CACHE_TYPES = ("filecache::2.0", "filecache::1.0", "prism::filecache")


def _is_sop_cache(node):
    tn = node.type().name().lower()
    return any(k in tn for k in FX_SOP_CACHE_TYPES)


def fx_sopcreate_for(node, cap=6000):
    """Le sopcreate LOP en amont d'un lop_filecache (contient le reseau SOP de sim/FX).
    None si aucun -> pas un setup FX (cfx = chaine LOP directe, pas de caches SOP)."""
    seen, stack = set(), [x for x in node.inputs() if x is not None]
    while stack and len(seen) < cap:
        n = stack.pop()
        if n.path() in seen:
            continue
        seen.add(n.path())
        if "sopcreate" in n.type().name().lower():
            return n
        stack.extend([x for x in n.inputs() if x is not None])
    return None


def _sop_upstream_set(node, cap=20000):
    """Nodes en amont via inputs() recursif (au sein d'un meme niveau de reseau)."""
    seen, stack = set(), [x for x in node.inputs() if x is not None]
    while stack and len(seen) < cap:
        n = stack.pop()
        if n.path() in seen:
            continue
        seen.add(n.path())
        stack.extend([x for x in n.inputs() if x is not None])
    return seen


def fx_sop_chain(sopcreate):
    """Liste ORDONNEE (amont->aval) des filecaches SOP disque atteignables sous le
    sopcreate, triee par nb de caches en amont (dependance mutuelle : un cache qui
    en alimente un autre passe avant). [] si aucun (HDA locked, ou setup cfx)."""
    if sopcreate is None:
        return []
    disk = [n for n in sopcreate.allSubChildren() if _is_sop_cache(n)]
    paths = {d.path() for d in disk}

    def upcount(d):
        return len(_sop_upstream_set(d) & paths)

    return sorted(disk, key=lambda d: (upcount(d), d.path()))


def fx_chain_for_cache(cache):
    """(sopcreate|None, [caches SOP ordonnes]) pour un lop_filecache donne."""
    cont = fx_sopcreate_for(cache)
    return cont, fx_sop_chain(cont)


def fx_opaque(sopcreate):
    """Le reseau du sopcreate est-il ILLISIBLE (on ne voit aucun node dedans) ?

    /!\\ C'est LA seule bonne definition de "sim inatteignable". On la deduisait avant de
    l'absence de filecache SOP -- ce qui confond deux choses tres differentes :
      - on ne voit pas dedans           -> on ne peut RIEN affirmer, on s'abstient ;
      - on voit dedans et il n'y a AUCUN cache -> il n'y a simplement rien a re-simuler
        (setup procedural, layer "still"...) -> il faut recacher normalement.
    Sur frederic_2603, `_OUT_still` expose 12 nodes sans aucun cache : la 2e situation.
    Et `isLockedHDA` ne discrimine pas : les deux sopcreate de cette scene le sont, l'un
    expose 380 nodes et 3 filecaches."""
    if sopcreate is None:
        return False
    try:
        return not sopcreate.allSubChildren()
    except Exception:
        return True  # illisible -> on s'abstient


def fx_chain_for_caches(caches):
    """(sopcreate|None, [caches SOP ordonnes], opaque) pour TOUS les caches d'un item.

    Un item peut porter plusieurs lop_filecache : ne regarder que le premier faisait
    rater la chaine SOP des autres (vu sur frederic_2603 : le 1er cache n'a aucun cache
    SOP, le 2e en a 3 -- l'item etait declare 'sim inatteignable' a cause du 1er)."""
    cont, chain, seen = None, [], set()
    conts = []
    for c in caches or []:
        sc = fx_sopcreate_for(c)
        if sc is None:
            continue
        if cont is None:
            cont = sc
        if sc.path() not in {x.path() for x in conts}:
            conts.append(sc)
        for n in fx_sop_chain(sc):
            if n.path() not in seen:
                seen.add(n.path())
                chain.append(n)
    # opaque seulement si AUCUN des sopcreate n'est lisible
    opaque = bool(conts) and all(fx_opaque(sc) for sc in conts)
    return cont, chain, opaque


def shot_label(pcore, imp, cfg):
    """Nom de shot 'propre' de l'import, independant du nom du node.

    /!\\ Dispatch par TYPE : un usd_layer_stack n'a pas de `filepath` -- sans ce test on
    retombait sur imp.name() ('sh010'), compare ensuite au shot resolu de la sortie
    ('SQ0010/SH0010') -> un faux ⚠ 'import=sh010 vs sortie=...' sur CHAQUE ligne."""
    if imp is None:
        return "?"
    if is_layer_stack(imp):
        return layer_stack_shot(imp) or imp.name()
    fp = parm_val(imp, cfg.get("import_path_parm", "filepath"))
    if not fp:
        return imp.name()
    try:
        data = pcore.paths.getCachePathData(fp) or {}
    except Exception:
        data = {}
    seq = data.get("sequence") or ""
    shot = data.get("shot") or ""
    if seq and shot:
        return "%s/%s" % (seq, shot)
    return shot or data.get("asset") or imp.name()


def shot_from_cache_output(pcore, cache):
    """Shot 'propre' depuis la SORTIE resolue du cache (Prism getOutputEntity),
    independant du cablage ET des noms de node. Retourne 'SEQ/SHOT' ou None.
    Marche meme quand la topologie ne relie pas le cache a un import (setups FX)."""
    usd = pcore.getPlugin("USD")
    ue = getattr(getattr(usd, "api", None), "usdExport", None) if usd else None
    if ue is None:
        return None
    try:
        st = ue.getStateFromNode({"node": cache})
        ui = getattr(st, "ui", None) if st is not None else None
        ent = ui.getOutputEntity() if ui and hasattr(ui, "getOutputEntity") else None
    except Exception:
        return None
    if isinstance(ent, dict):
        seq, shot = ent.get("sequence"), ent.get("shot")
        if seq and shot:
            return "%s/%s" % (seq, shot)
        return shot or ent.get("asset")
    return None


def name_shot_mismatch(node_name, resolved_shot):
    """(has_token, mismatch) : le nom du node contient-il un token 'shNNN', et
    contredit-il le shot resolu ? Comparaison souple sur les chiffres (sh010==SH0010)."""
    if not resolved_shot:
        return False, False
    shot = resolved_shot.split("/")[-1]
    m = re.search(r"(?i)sh\d{2,4}", node_name or "")
    if not m:
        return False, False
    nd = re.sub(r"\D", "", m.group(0)).lstrip("0")
    td = re.sub(r"\D", "", shot).lstrip("0")
    return True, (nd != td)


def pair_import(hou, pcore, cfg, anchor, shot, imports, tracked, extra=None):
    """Retrouve l'import qui alimente `anchor`. Retourne (import|None, ambigu, methode).

    1) TOPOLOGIE d'abord : seul l'import REELLEMENT CABLE compte. Les autres imports de
       la scene (residus de l'ancien setup, doublons) ne concernent pas ce node, meme
       s'ils portent le meme shot.
    2) `extra` = un 2e node par ou tenter la remontee (ex : le filecache d'un shot quand
       l'ancre est son render).
    3) repli par SHOT : indispensable sur les setups FX, ou des caches SOP figes coupent
       la chaine LOP et la topologie ne remonte a aucun import."""
    for node in [n for n in (anchor, extra) if n is not None]:
        ups = upstream_import(hou, node, cfg)
        if len(ups) == 1:
            return ups[0], False, "topologie"
        if len(ups) > 1:
            # plusieurs imports cables (branche partagee) -> departage par SHOT, puis
            # par presence du layer tracke
            same = [u for u in ups if shot != "?" and shot_label(pcore, u, cfg) == shot]
            pool = same or ups
            withlayer = [
                u
                for u in pool
                if _import_has_layer({"layers": import_layers(u)}, tracked)
            ]
            chosen = (withlayer or pool)[0]
            return (
                chosen,
                len(withlayer or pool) > 1,
                "topologie+shot" if same else "topologie-ambigu",
            )
    imp, ambig = import_for_shot(imports, shot, tracked, cfg.get("exported_imports"))
    return imp, ambig, ("shot" if imp is not None else None)


def discover_pairs(hou, pcore, cfg):
    """Un ITEM = le LIVRABLE d'un shot dans CETTE scene, et on s'ancre dessus :

      - scene de RENDU (lighting, confo...) -> l'ancre est le `prism::LOP_Render`. Le
        filecache du meme shot, s'il existe, n'est qu'une ETAPE AVANT (on le re-cache,
        puis on soumet le render).
      - scene de CACHE (cfx, fx) -> pas de render : l'ancre est le `lop_filecache`.

    S'ancrer sur le cache dans une scene de rendu etait un contresens : une scene Confo
    (7 LOP_Render, 0 filecache) ne remontait AUCUN item.

    Appariement de l'import : voir pair_import (topologie d'abord, shot en repli).
    Cross-checks de nommage -> warnings non bloquants."""
    stage_root = cfg.get("stage_root", "/stage")
    cache_type = cfg.get("cache_node_type", "prism::lop_filecache").lower()
    tracked = cfg.get("tracked_layer", "_layer_anm_master")
    root = hou.node(stage_root)
    items = []
    if root is None:
        return items
    imports = collect_imports(hou, pcore, cfg)  # une seule passe pour toute la scene
    renders = collect_renders(hou, cfg)  # LOP_Render (vide sur une scene cfx/fx)
    caches = [n for n in root.allSubChildren() if cache_type in n.type().name().lower()]

    # imports REELLEMENT en amont d'un export (cache ou render) : sert a departager le
    # repli par shot. Sur la scene FX de frederic_2603, 1 import sur 77 est concerne --
    # les 76 autres sont des stacks camera qui n'alimentent aucun export.
    exported = set()
    for anchor in caches + [r["node"] for r in renders]:
        for u in upstream_import(hou, anchor, cfg):
            exported.add(u.path())
    cfg["exported_imports"] = exported

    # index des caches par shot (leur sortie Prism, pas leur nom)
    cache_by_shot = {}
    for c in caches:
        cache_by_shot.setdefault(shot_from_cache_output(pcore, c) or "?", []).append(c)

    def build(anchor, shot, cnodes, rnodes, kind):
        cnodes = [c for c in (cnodes or []) if c is not None]
        cache = cnodes[0] if cnodes else None
        imp, ambig, method = pair_import(
            hou, pcore, cfg, anchor, shot, imports, tracked, extra=cache
        )
        shot_imp = shot_label(pcore, imp, cfg) if imp is not None else None
        if shot == "?" and shot_imp:
            shot = shot_imp  # ancre muette -> on retombe sur le shot de l'import
        warns, notes = [], []
        if imp is None:
            warns.append("aucun import pour ce shot")
        if ambig:
            warns.append("plusieurs imports pour ce shot (pris celui avec le layer)")
        if shot != "?" and shot_imp and shot != shot_imp:
            warns.append("import=%s vs sortie=%s" % (shot_imp, shot))
        has_tok, mism = name_shot_mismatch(anchor.name(), shot)
        if mism:
            warns.append("nom '%s' != shot %s" % (anchor.name(), shot))
        elif shot != "?" and not has_tok:
            notes.append("shot deduit de la sortie (node non nomme)")
        if imp is not None:
            _, imism = name_shot_mismatch(imp.name(), shot_imp or shot)
            if imism:
                warns.append(
                    "nom import '%s' != %s importe" % (imp.name(), shot_imp or shot)
                )
        # chaine de caches SOP a re-simuler (setups FX) ; [] sans cache ou en cfx direct.
        # Sur TOUS les caches de l'item, pas seulement le premier.
        sopcreate, sop_chain, opaque = fx_chain_for_caches(cnodes)
        items.append(
            {
                "id": anchor.name(),
                "anchor": kind,  # "render" | "cache"
                "cache": cache,  # 1er cache (compat) ; peut etre None
                "caches": cnodes,  # TOUS les caches du shot : un shot peut en avoir
                # plusieurs, publiant des produits DIFFERENTS (verifie sur
                # frederic_2603 : _layer_fx_snow_still ET _layer_fx_snow_sim). On n'en
                # attachait qu'un -> l'autre n'etait jamais re-cache.
                "import": imp,
                "shot": shot,
                "pair_method": method,
                "fx_sopcreate": sopcreate,
                "fx_chain": sop_chain,
                "fx_opaque": opaque,  # reseau de sim illisible -> on ne peut rien affirmer
                "renders": rnodes,
                "warn": "  |  ".join(warns),
                "note": "  |  ".join(notes),
            }
        )

    # --- 1) ancre RENDER : un item par shot rendu (le livrable de la scene) ---------
    # groupe par SHOT -> cache + render(s) du meme shot = UNE ligne (cocher = re-cache
    # puis render). Un shot non resolu ('?') n'est PAS groupe : on ne fusionne pas des
    # nodes sans rapport.
    by_shot = {}
    for r in renders:
        s = r.get("shot") or "?"
        by_shot.setdefault(s if s != "?" else r["node"].path(), []).append(r["node"])
    rendered_shots = {r.get("shot") for r in renders if r.get("shot")}
    for key, rnodes in by_shot.items():
        shot = next((r.get("shot") for r in renders if r["node"] is rnodes[0]), None)
        shot = shot or "?"
        cnodes = cache_by_shot.get(shot) or [] if shot != "?" else []
        build(rnodes[0], shot, cnodes, rnodes, "render")

    # --- 2) caches dont le shot n'est PAS rendu ici -> ancre cache (cfx/fx) ---------
    for shot, cnodes in cache_by_shot.items():
        if shot in rendered_shots:
            continue  # deja couvert par l'item render de ce shot
        for c in cnodes:
            build(c, shot, [c], renders_for_shot(renders, shot), "cache")

    items.sort(key=lambda it: it["id"])
    return items


def _serialize_fx_chain(item):
    """Chaine de caches SOP de l'item, en dicts JSON pour l'UI (ordre = topologique).
    'rel' = chemin court sous le sopcreate (lisible dans l'UI)."""
    cont = item.get("fx_sopcreate")
    base = cont.path() if cont is not None else ""
    out = []
    for nd in item.get("fx_chain", []):
        p = nd.path()
        out.append(
            {
                "name": nd.name(),
                "path": p,
                "rel": ("." + p[len(base) :]) if base and p.startswith(base) else p,
                "type": nd.type().name(),
                "prism": "prism::filecache" in nd.type().name().lower(),
            }
        )
    return out


# --------------------------------------------------------------------------- #
#  LOP_Render : submit farm (Deadline) des renders lighting du shot
#
#  Une scene lighting a, par shot, un prism::LOP_Render (usdrender_rop / husk / Karma
#  -> Deadline). L'outil peut, apres avoir bumpe l'import + re-cache le LightingCache,
#  RE-SOUMETTRE le render a la ferme -- exactement l'action que l'artiste fait avec le
#  bouton "execute" quand "submitJob" est coche.
#
#  Appariement au shot SANS API render incertaine : on lit le parm 'customContext' du
#  node (JSON Prism {sequence, shot, ...}), pose par le node lui-meme. Fallback : le
#  parm 'context' ("Shot - SQ0010-SH0050").
#
#  /!\ SECURITE : presser 'execute' avec submitJob=OFF lance un render LOCAL dans
#  hython (bloque des heures, faux). submit_render() FORCE submitJob=1 et REFUSE de
#  presser sinon. On ne rend jamais en local par megarde.
# --------------------------------------------------------------------------- #
def shot_of_render(node):
    """'SEQ/SHOT' d'un prism::LOP_Render, depuis son parm 'customContext' (JSON Prism),
    sinon depuis 'context' ('Shot - SQ0010-SH0050'). None si indeterminable."""
    cc = parm_val(node, "customContext")
    if cc:
        try:
            d = json.loads(cc)
            seq, shot = d.get("sequence"), d.get("shot")
            if seq and shot:
                return "%s/%s" % (seq, shot)
            if d.get("hierarchy"):
                return d["hierarchy"]
        except Exception:
            pass
    ctx = parm_val(node, "context") or ""
    m = re.search(r"([A-Za-z]+\d+)[-/]([A-Za-z]+\d+)", ctx)
    if m:
        return "%s/%s" % (m.group(1), m.group(2))
    return None


def collect_renders(hou, cfg):
    """Tous les prism::LOP_Render de la scene avec le shot qu'ils rendent (lu depuis
    leurs parms, pas depuis le nom). [] si aucun (scene sans render, ex cfx/fx pur)."""
    stage_root = cfg.get("stage_root", "/stage")
    rtype = cfg.get("render_node_type", "prism::LOP_Render").lower()
    root = hou.node(stage_root)
    out = []
    if root is None:
        return out
    for n in root.allSubChildren():
        # le type EXACT du node de tete (pas les usdrender_rop internes)
        if rtype in n.type().name().lower():
            out.append({"node": n, "shot": shot_of_render(n)})
    return out


def renders_for_shot(renders, shot):
    """Les nodes render dont le shot resolu == `shot`. [] si aucun."""
    if not shot or shot == "?":
        return []
    return [r["node"] for r in renders if r.get("shot") == shot]


def read_render_executions(node):
    """Executions d'un LOP_Render = son multiparm `executions` (chacune rend UN layer,
    context option `layer` = CHARS/BG/FG/MG/VOLUME...). Retourne
    [{index, layer, enabled}] (index 1-based ; enabled = le toggle Enabled du node).
    L'outil ne gere PAS les layers, il expose juste les executions du node telles quelles."""
    out = []
    cnt = parm_val(node, "executions")
    if not cnt:
        return out
    for i in range(1, int(cnt) + 1):
        enabled = bool(parm_val(node, "execution_enabled_%d" % i))
        layer = None
        nco = parm_val(node, "contextOptions_%d" % i) or 0
        for j in range(1, int(nco) + 1):
            if parm_val(node, "contextOptionsName_%d_%d" % (i, j)) == "layer":
                layer = parm_val(node, "contextOptionsValue_%d_%d" % (i, j))
                break
        out.append({"index": i, "layer": layer or ("exec %d" % i), "enabled": enabled})
    return out


def set_render_executions(node, enabled_layers):
    """Active `execution_enabled_#` pour les executions dont le layer est dans
    `enabled_layers` (par NOM de layer), desactive les autres. Modifie le node -> part
    dans le version-up. Retourne (n_actives, n_total). enabled_layers=None -> ne touche
    a rien (garde l'etat du node)."""
    execs = read_render_executions(node)
    if enabled_layers is None:
        return sum(1 for e in execs if e["enabled"]), len(execs)
    want = set(enabled_layers)
    n_on = 0
    for e in execs:
        on = e["layer"] in want
        set_parm(node, "execution_enabled_%d" % e["index"], 1 if on else 0)
        n_on += on
    return n_on, len(execs)


def _serialize_renders(item, pcore=None):
    """Nodes render de l'item + leurs executions (layers cochables) + leurs reglages
    ferme actuels (ceux que la fenetre de submit Prism montrerait), en JSON pour l'UI."""
    out = []
    for nd in item.get("renders", []) or []:
        d = {
            "name": nd.name(),
            "path": nd.path(),
            "type": nd.type().name(),
            "executions": read_render_executions(nd),
        }
        if pcore is not None:
            try:
                d["farm"] = read_farm_settings(render_state(pcore, nd).ui)
            except Exception as e:  # jamais bloquant pour le status
                d["farm_error"] = "%s: %s" % (type(e).__name__, e)
        out.append(d)
    return out


# --------------------------------------------------------------------------- #
#  Reglages ferme (Deadline) d'un LOP_Render
# --------------------------------------------------------------------------- #
# Tout ce que Deadline recoit (frames, prio, chunk, pool, group, machine limit, job haute
# prio...) est LU sur les widgets du state Prism au moment du publish
# (Prism_Deadline_Functions.sm_render_submitJob). La fenetre de submit GUI ne fait rien
# d'autre que montrer ces widgets a l'artiste : les regler ici = ce qu'il ferait a la
# main. Verifie par dry-run (envoi a Deadline intercepte) : prio, frames, chunk, machine
# limit et split du job haute prio arrivent tels quels dans les jobs.
# Une cle ABSENTE d'un override garde la valeur de la scene (chaque node a les siennes :
# prio 65 / 60 selon le shot sur beaverDam).


class FarmSettingError(Exception):
    """Reglage ferme impossible a appliquer : on REFUSE le submit plutot que d'envoyer
    autre chose que ce que l'utilisateur a demande."""


def render_state(pcore, node):
    """State Prism d'un prism::LOP_Render (celui que montre la fenetre de submit)."""
    usd = pcore.getPlugin("USD") if pcore is not None else None
    lr = getattr(getattr(usd, "api", None), "lopRender", None) if usd else None
    if lr is None or not hasattr(lr, "getStateFromNode"):
        raise RuntimeError("render %s : API lopRender indisponible" % node.path())
    state = lr.getStateFromNode({"node": node})
    if getattr(state, "ui", None) is None:
        raise RuntimeError("render %s : state sans ui" % node.path())
    return state


def _combo_items(cb):
    return [cb.itemText(i) for i in range(cb.count())] if cb is not None else []


def resolve_frame_tokens(expr, first, last):
    """'{first},{middle},{last}' / '{first}-{last}x10' -> expression Prism concrete pour la
    plage first..last DE CE SHOT. middle = celui du job haute prio de Prism (milieu de la
    liste des frames). Une expression sans token est rendue telle quelle."""
    frames = list(range(int(first), int(last) + 1)) or [int(first)]
    middle = frames[int((len(frames) - 1) / 2)]
    return (expr or "").format(first=frames[0], middle=middle, last=frames[-1])


def read_farm_settings(ui):
    """Reglages ferme ACTUELS d'un state LOP render (+ les choix possibles)."""

    def val(name, kind):
        w = getattr(ui, name, None)
        if w is None:
            return None
        if kind == "spin":
            return w.value()
        if kind == "check":
            return bool(w.isChecked())
        if kind == "combo":
            return w.currentText()
        return w.text()

    rt = val("cb_rangeType", "combo") or ""
    first = last = None
    try:
        fr = ui.getFrameRange(rt) if rt else None
        if fr and rt == "Expression":
            first, last = int(min(fr)), int(max(fr))
        elif fr:
            first = int(fr[0])
            last = first if rt == "Single Frame" else int(fr[1])
    except Exception:
        pass
    hp = getattr(ui, "gb_prioJob", None)
    return {
        "range_type": rt,
        "first": first,
        "last": last,
        "expression": val("le_frameExpression", "text") or "",
        "priority": val("sp_rjPrio", "spin"),
        "chunk": val("sp_rjFramesPerTask", "spin"),
        "timeout": val("sp_rjTimeout", "spin"),
        "suspended": val("chb_rjSuspended", "check"),
        "concurrent": val("sp_dlConcurrentTasks", "spin"),
        "machine_limit": val("sp_machineLimit", "spin"),
        "pool_preset": val("cb_dlPreset", "combo"),
        "pool": val("cb_dlPool", "combo"),
        "secondary_pool": val("cb_sndPool", "combo"),
        "group": val("cb_dlGroup", "combo"),
        "pools": _combo_items(getattr(ui, "cb_dlPool", None)),
        "groups": _combo_items(getattr(ui, "cb_dlGroup", None)),
        "high_prio": {
            "enabled": bool(hp is not None and hp.isChecked()),
            "priority": val("sp_highPrio", "spin"),
            "frames": val("e_highPrioFrames", "text") or "",
        },
        # le job de rendu husk prend son groupe dans l'env du projet s'il y est
        # (pipeline.json frederic : PRISM_HUSK_DEADLINE_GROUP=husk_grp, vu sur un job GUI)
        "husk_group_env": os.environ.get("PRISM_HUSK_DEADLINE_GROUP") or "",
    }


def apply_farm_settings(ui, ov, core=None):
    """Applique les overrides `ov` sur le state (cles absentes = valeur de la scene).
    Retourne la liste lisible de ce qui a ete regle. FarmSettingError si une valeur est
    impossible (pool inconnu, prio hors bornes...) : l'appelant ne soumet rien."""
    if not ov:
        return []
    done = []

    def widget(name, label):
        w = getattr(ui, name, None)
        if w is None:
            raise FarmSettingError("%s : reglage absent de ce render" % label)
        return w

    def spin(name, value, label):
        w = widget(name, label)
        v = int(value)
        if v < w.minimum() or v > w.maximum():
            raise FarmSettingError(
                "%s %s hors bornes [%s..%s]" % (label, v, w.minimum(), w.maximum())
            )
        w.setValue(v)
        done.append("%s=%s" % (label, v))

    def combo(name, value, label):
        w = widget(name, label)
        idx = w.findText(value)
        if idx < 0:
            raise FarmSettingError(
                "%s '%s' inconnu de Deadline (choix : %s)"
                % (label, value, ", ".join(_combo_items(w)))
            )
        w.setCurrentIndex(idx)
        done.append("%s=%s" % (label, value))

    # --- frames ---
    fr = ov.get("frames") or {}
    mode = fr.get("mode")
    if mode == "range":
        a, b = int(fr["start"]), int(fr["end"])
        if a > b:
            raise FarmSettingError("frames : debut %s > fin %s" % (a, b))
        combo("cb_rangeType", "Custom", "type de plage")
        done.pop()
        spin("sp_rangeStart", a, "debut")
        spin("sp_rangeEnd", b, "fin")
        done[-2:] = ["frames=%s-%s" % (a, b)]
    elif mode == "expression":
        cur = read_farm_settings(ui)
        if cur["first"] is None:
            raise FarmSettingError("frames : plage du shot illisible")
        try:
            expr = resolve_frame_tokens(fr.get("expr") or "", cur["first"], cur["last"])
        except (KeyError, IndexError, ValueError) as e:
            raise FarmSettingError("frames : expression invalide (%s)" % e)
        if core is not None:
            try:
                resolved = core.resolveFrameExpression(expr)
            except Exception:
                resolved = None
            if not resolved:
                raise FarmSettingError("frames : expression illisible '%s'" % expr)
        combo("cb_rangeType", "Expression", "type de plage")
        done.pop()
        widget("le_frameExpression", "expression").setText(expr)
        done.append("frames=%s" % expr)
    elif mode:
        raise FarmSettingError("frames : mode inconnu '%s'" % mode)

    for name, key, label in (
        ("sp_rjPrio", "priority", "priority"),
        ("sp_rjFramesPerTask", "chunk", "frames/task"),
        ("sp_rjTimeout", "timeout", "timeout"),
        ("sp_dlConcurrentTasks", "concurrent", "concurrent tasks"),
        ("sp_machineLimit", "machine_limit", "machine limit"),
    ):
        if ov.get(key) is not None:
            spin(name, ov[key], label)
    for name, key, label in (
        ("cb_dlPool", "pool", "pool"),
        ("cb_sndPool", "secondary_pool", "secondary pool"),
        ("cb_dlGroup", "group", "group"),
    ):
        if ov.get(key):
            combo(name, ov[key], label)
    if ov.get("suspended") is not None:
        widget("chb_rjSuspended", "suspended").setChecked(bool(ov["suspended"]))
        done.append("suspended=%s" % bool(ov["suspended"]))
    hp = ov.get("high_prio") or {}
    if hp:
        gb = widget("gb_prioJob", "job haute prio")
        if hp.get("enabled") is not None:
            gb.setChecked(bool(hp["enabled"]))
            done.append("high prio job=%s" % ("on" if hp["enabled"] else "off"))
        if hp.get("priority") is not None:
            spin("sp_highPrio", hp["priority"], "high prio")
        if hp.get("frames"):
            widget("e_highPrioFrames", "frames haute prio").setText(hp["frames"])
            done.append("high prio frames=%s" % hp["frames"])
    return done


def farm_summary(ui):
    """Une ligne : ce que Deadline va recevoir pour ce render (apres overrides)."""
    s = read_farm_settings(ui)
    if s["range_type"] == "Expression":
        frames = s["expression"]
    else:
        frames = "%s-%s (%s)" % (s["first"], s["last"], s["range_type"])
    hp = s["high_prio"]
    husk = s["husk_group_env"]
    parts = [
        "frames %s" % frames,
        "prio %s" % s["priority"],
        "%s frame(s)/task" % s["chunk"],
        "pool %s" % s["pool"],
        "group %s%s"
        % (s["group"], " (job husk : %s via le projet)" % husk if husk else ""),
        "machine limit %s" % s["machine_limit"],
    ]
    if s["suspended"]:
        parts.append("SUSPENDED")
    parts.append(
        "job haute prio %s sur %s" % (hp["priority"], hp["frames"])
        if hp["enabled"]
        else "pas de job haute prio"
    )
    return " | ".join(parts)


def prerender_gui_effects(pcore, node):
    """Parite GUI du hook projet `preRender` : sa branche GUI pose ILLOGIC_TEMP_NODE (layers
    -> shot/OPTI des executions actives) ; sans interface (hou.isUIAvailable() faux) il
    sort AVANT. On rejoue cet effet avec SA fonction `catchInfo` (le code du projet, pas
    une copie) -> meme valeur qu'un submit GUI. Rien si le hook ou la fonction n'existe
    pas. (Aujourd'hui seul Hooks/old/preSubmit_Deadline.py la lisait : desactive.)"""
    try:
        hook_dir = pcore.projects.getHookFolder()
        if not os.path.isfile(os.path.join(hook_dir, "preRender.py")):
            return None
        if hook_dir not in sys.path:
            sys.path.append(hook_dir)
        # meme import que Prism (Callbacks.callHook : __import__(hookName))
        hook = sys.modules.get("preRender") or __import__("preRender")
        catch = getattr(hook, "catchInfo", None)
        if catch is None or node.type().name() != "prism::LOP_Render::1.0":
            return None
        val = str(catch(node))
        os.environ["ILLOGIC_TEMP_NODE"] = val
        return val
    except Exception as e:
        log("    (parite preRender : %s)" % e)
        return None


def submit_render(pcore, node, comment=None, farm=None):
    """Soumet un prism::LOP_Render a la FERME Deadline, EN HEADLESS.

    Pourquoi pas le bouton 'execute' : `lopRender.executePressed` ouvre (submitJob on)
    le dialogue Farm_Submitter, qui ne s'`.show()` pas en headless -> AUCUN job (verifie :
    un apply reel a logue '1 OK' sans creer de job). On replique donc ce que fait le
    bouton Submit du dialogue, `Farm_Submitter.submit()` (source Prism), SANS UI :
        state = lopRender.getStateFromNode(node)
        state.ui.gb_submit.setChecked(True)        # <- FARM (False = render local)
        sm.publish(executeState=True, states=[state], sanityChecks=<parm du node>, ...)
    C'est `gb_submit` (pas le bouton) qui decide farm-vs-local -> on le coche EXPLICITEMENT
    et on REFUSE si on ne peut pas (pas de submitter farm / pas de gb_submit / pas de SM)
    -> jamais de render local par megarde.

    `farm` = overrides des reglages ferme (cf apply_farm_settings) : poses sur les MEMES
    widgets que l'artiste regle dans la fenetre de submit.

    Parite avec un submit GUI (audit 16/10) : memes callbacks/hooks (sm.publish les
    declenche), plus ce que la GUI fait et que le headless sautait :
      - sanityChecks : celui du NODE (Farm_Submitter lit le parm), plus force a False ;
      - le node est SELECTIONNE (le check studio TileFramePerTask ne regarde que la
        selection : sans ca il ne verifiait rien) ;
      - la branche GUI du hook preRender (prerender_gui_effects) ;
      - un sanity check studio en ERROR refuse le submit (la GUI grise 'Publish
        anyways') au lieu de geler hython (headless_guard)."""
    # Farm_Submitter.submit lit sanityChecks sur le node : on le lit AVANT d'y toucher
    p_sanity = node.parm("sanityChecks")
    sanity = bool(p_sanity.eval()) if p_sanity is not None else True

    # le node reflete l'intention 'submit' + rien qui sauve le hip / popupe en headless
    # (la scene est deja sauvee par l'outil, et saveScene/incrementScene sont aussi
    # passes a False au publish)
    set_parm(node, "submitJob", 1)
    for pn, val in (
        ("saveScene", 0),
        ("incrementScene", 0),
        ("showSuccessPopup", 0),
    ):
        set_parm(node, pn, val)

    state = render_state(pcore, node)
    ui = state.ui

    # 1) le switch FARM : gb_submit (comme Farm_Submitter.submit)
    gb = getattr(ui, "gb_submit", None)
    if gb is None:
        raise RuntimeError(
            "render %s : state sans gb_submit -> REFUS (pas de render local)"
            % node.path()
        )
    # 2) un submitter FARM doit exister (Deadline), sinon publish() rendrait EN LOCAL
    cb = getattr(ui, "cb_manager", None)
    n_mgr = cb.count() if cb is not None else 0
    if not n_mgr:
        raise RuntimeError(
            "render %s : aucun submitter farm installe (cb_manager vide) -> REFUS "
            "(publish rendrait en local)" % node.path()
        )
    picked = None
    for i in range(n_mgr):
        if "deadline" in cb.itemText(i).lower():
            cb.setCurrentIndex(i)
            picked = cb.itemText(i)
            break
    picked = picked or cb.currentText()
    try:
        gb.setCheckable(True)
        gb.setChecked(True)
    except Exception as e:
        raise RuntimeError("render %s : gb_submit non cochable (%s)" % (node.path(), e))
    if not gb.isChecked():
        raise RuntimeError(
            "render %s : gb_submit refuse True -> REFUS (jamais de render local)"
            % node.path()
        )

    # 3) reglages ferme demandes (APRES le choix du manager : il recree ses widgets)
    applied = apply_farm_settings(ui, farm, core=pcore)
    if applied:
        log("    reglages ferme demandes : %s" % ", ".join(applied))
    log("    job(s) Deadline : %s" % farm_summary(ui))

    # 4) State Manager (headless : create=True au besoin)
    sm = pcore.getStateManager()
    if sm is None and hasattr(pcore, "getStateManager"):
        try:
            sm = pcore.getStateManager(create=True)
        except Exception:
            sm = None
    if sm is None or not hasattr(sm, "publish"):
        raise RuntimeError(
            "render %s : StateManager indisponible en headless -> submit impossible"
            % node.path()
        )

    # 5) parite GUI : node selectionne + effets GUI du hook preRender
    try:
        node.setSelected(True, clear_all_selected=True)
    except Exception:
        pass
    temp_node = prerender_gui_effects(pcore, node)
    if temp_node is not None:
        log("    hook preRender (branche GUI) : ILLOGIC_TEMP_NODE=%s" % temp_node)

    # NB: ne PAS appeler state.text() -- un state Prism herite de QTreeWidgetItem dont
    # text(col) exige un argument (plantait le submit AVANT tout publish).
    log(
        "    submit(headless) : farm=%s  gb_submit=%s  sanityChecks=%s"
        % (picked, gb.isChecked(), sanity)
    )
    # commentaire EXPLICITE : sans lui, publish() prend e_comment.text() du State Manager,
    # vide en headless -> le versioninfo du render avait "comment": "" (vu sur SH0060).
    n_dialogs = len(headless_guard.DIALOGS)
    result = sm.publish(
        executeState=True,
        states=[state],
        comment=comment,
        successPopup=False,
        saveScene=False,
        incrementScene=False,
        sanityChecks=sanity,
        versionWarning=False,
    )
    refused = headless_guard.refused_since(n_dialogs)
    if refused:
        raise RuntimeError(
            "submit refuse : %s"
            % " ; ".join(headless_guard.describe(d) for d in refused)
        )
    if result is None:
        # publish() sort SANS rien executer quand un hook prePublish annule
        raise RuntimeError("submit annule avant l'envoi (hook prePublish)")
    if result is False:
        infos = []
        for r in getattr(sm, "publishResult", None) or []:
            res = r.get("result") if isinstance(r, dict) else None
            infos.append(str(res[0]) if res else "erreur inconnue")
        raise RuntimeError(
            "Prism signale des erreurs pendant le submit (%s) : verifier les jobs dans "
            "Deadline" % (" | ".join(infos) or "voir le log au-dessus")
        )
    return "sm.publish(gb_submit=True -> %s) -> %r" % (picked, result)


def _plan_entries(plan, item_id):
    """Normalise le render_plan d'un item -> [{node, layers}]. layers=None -> ne touche
    pas aux executions (submit tel quel). Tolere l'ancien format (liste de chemins)."""
    out = []
    for e in plan.get(item_id) or []:
        if isinstance(e, str):
            out.append({"node": e, "layers": None})
        elif isinstance(e, dict) and e.get("node"):
            out.append({"node": e["node"], "layers": e.get("layers")})
    return out


def apply_render_selections(hou, items, reports, cfg):
    """AVANT le save : ecrit l'etat Enabled des executions de chaque render selectionne
    (par NOM de layer) -> part dans le version-up (behavior 2). Ne touche qu'aux items
    dont le re-cache a abouti. Ne SOUMET rien."""
    plan = cfg.get("render_plan") or {}
    rep_by_id = {r.get("id"): r for r in reports}
    for it in items:
        rep = rep_by_id.get(it["id"], {})
        if rep.get("ok") is False or rep.get("skipped_locked"):
            continue
        for entry in _plan_entries(plan, it["id"]):
            if entry["layers"] is None:
                continue
            nd = hou.node(entry["node"])
            if nd is None:
                continue
            n_on, tot = set_render_executions(nd, entry["layers"])
            log(
                "  render %s : %d/%d layer(s) actifs -> %s"
                % (nd.name(), n_on, tot, ", ".join(entry["layers"]) or "(aucun)")
            )


def submit_renders(hou, pcore, items, reports, cfg):
    """2e passe (APRES le save version-up) : soumet a la ferme les renders selectionnes
    (cfg['render_plan'] = {item_id: [{node, layers}]}). Les executions/layers ont deja
    ete ecrites par apply_render_selections AVANT le save (behavior 2). On soumet APRES le
    save pour que la ferme rende la scene bumpee/sauvee. On NE soumet PAS le render d'un
    shot dont le re-cache a echoue (donnee cassee) ni un render dont AUCUN layer n'est
    coche (rien a rendre)."""
    plan = cfg.get("render_plan") or {}
    # reglages ferme demandes depuis l'UI : les memes pour tous les renders soumis ("*")
    farm = (cfg.get("farm_plan") or {}).get("*") or None
    rep_by_id = {r.get("id"): r for r in reports}
    log("-" * 70)
    log("SUBMIT RENDERS (ferme Deadline)")
    if farm:
        log("Reglages ferme demandes : %s" % json.dumps(farm, sort_keys=True))
    if not os.environ.get("PRISM_LAUNCH_ENV"):
        # un submit GUI copie dans le job l'env du profil du launcher Prism (OCIO...) :
        # ici il n'arrive que si l'outil a ete lance depuis le shelf Houdini
        log(
            "ATTENTION : PRISM_LAUNCH_ENV absent (outil lance hors de Houdini ?) -> les "
            "jobs n'auront pas l'environnement du profil launcher (OCIO...)."
        )
    n_ok = n_ko = 0
    for it in items:
        entries = _plan_entries(plan, it["id"])
        if not entries:
            continue
        rep = rep_by_id.get(it["id"], {})
        # ne rendre QUE des donnees saines : on saute si le re-cache a echoue (ok=False)
        # ou a ete saute sans bumper (locked-skip : import perime).
        if rep.get("ok") is False or rep.get("skipped_locked"):
            log("  %s : re-cache non abouti -> renders NON soumis" % it["id"])
            n_ko += len(entries)
            continue
        for entry in entries:
            nd = hou.node(entry["node"])
            if nd is None:
                log("  render introuvable: %s" % entry["node"])
                n_ko += 1
                continue
            if entry["layers"] is not None and not entry["layers"]:
                log("  %s : aucun layer coche -> render NON soumis" % nd.name())
                continue
            try:
                _t = time.perf_counter()
                log("  render %s [%s]" % (nd.name(), it["shot"]))
                res = submit_render(pcore, nd, cfg.get("render_comment"), farm=farm)
                span = _span(_t)
                errs = node_errors(nd)
                if errs:
                    log("  SUBMIT KO %s: %s" % (nd.name(), " | ".join(errs)))
                    n_ko += 1
                else:
                    log(
                        "  submit %s [%s] (%s) -> %s"
                        % (nd.name(), it["shot"], span, res)
                    )
                    n_ok += 1
            except FarmSettingError as ex:
                log("  SUBMIT REFUSE %s (reglages ferme) : %s" % (nd.name(), ex))
                n_ko += 1
            except Exception as ex:
                log("  SUBMIT KO %s: %s" % (entry["node"], ex))
                n_ko += 1
    log("Renders soumis: %d OK, %d KO" % (n_ok, n_ko))
    return n_ok, n_ko


def status_item(hou, pcore, item, cfg):
    """Etat read-only d'un item pour l'UI (JSON). Ne modifie rien."""
    tracked_list = tracked_layers(cfg)
    tracked = tracked_list[0]
    cont = item.get("fx_sopcreate")
    d = {
        "id": item["id"],
        "shot": item["shot"],
        "cache_node": item["cache"].path() if item.get("cache") is not None else None,
        # TOUS les caches du shot (il peut y en avoir plusieurs, cf discover_pairs), avec
        # le produit que chacun publie : c'est ce que l'artiste doit voir pour choisir,
        # bien plus parlant qu'un nom de node ('lop_filecache3').
        "caches": [
            {
                "path": c.path(),
                "name": c.name(),
                "product": cache_product(c, pcore) or "",
            }
            for c in (item.get("caches") or [])
        ],
        "anchor": item.get("anchor", "cache"),
        "import_node": item["import"].path() if item["import"] else None,
        # type de l'import : un prism::LOP_Import EPINGLE son chemin, un usd_layer_stack se
        # re-resout au latest -> seul le premier garde l'ancienne stack si on ne sauve pas
        "import_type": item["import"].type().name() if item["import"] else None,
        "pair_method": item.get("pair_method"),
        "tracked_layer": tracked,
        "tracked_layers": tracked_list,
        "tracked_mode": cfg.get("tracked_mode") or "or",
        "fx_sopcreate": cont.path() if cont is not None else None,
        "fx_chain": _serialize_fx_chain(item),
        "renders": _serialize_renders(item, pcore),
        "consumed_version": None,
        "latest_version": None,
        "stack_consumed": None,
        "stack_latest": None,
        "stale": None,
        "state": "error",
        "warn": item.get("warn", ""),
        "note": item.get("note", ""),
        "error": "",
    }
    if item["import"] is None:
        # cache sans import (ex: setup FX) : le shot est connu par la sortie, mais la
        # peremption par layer n'est pas calculable par cette methode -> etat benin.
        d["state"] = "no_import"
        return d
    st = compute_state(pcore, item["import"], cfg, shot=item.get("shot"))
    d["consumed_version"] = (
        ("v%03d" % st["consumed"]) if st["consumed"] is not None else None
    )
    d["latest_version"] = ("v%03d" % st["latest"]) if st["latest"] is not None else None
    d["import_path"] = st.get("cur")  # container USD consomme -> preview sans Houdini
    d["stack_consumed"] = st["stack_consumed"]
    d["stack_latest"] = st["stack_latest"]
    d["stale"] = st["stale"]
    d["layers"] = {
        name: {
            "consumed": ("v%03d" % ld["consumed"])
            if ld["consumed"] is not None
            else None,
            "latest": ("v%03d" % ld["latest"]) if ld["latest"] is not None else None,
            "stale": ld["stale"],
            # epingle dans le usd_layer_stack (cf preview.mark_pins)
            **(
                {"pinned": ld["pinned"], "pinned_behind": bool(ld.get("pinned_behind"))}
                if ld.get("pinned")
                else {}
            ),
        }
        for name, ld in (st.get("layers") or {}).items()
    }
    if st["err"]:
        d["error"] = st["err"]
    d["trust"] = st.get(
        "trust", ""
    )  # verified / uncertain / none (fiabilite du releve)
    d["ignored_layers"] = st.get("ignored") or []  # suivis mais non consommes ici
    d["deciding_layer"] = st.get("deciding")
    # pins du usd_layer_stack : gardes dans le snapshot -> le preview (disque seul, qui
    # ne voit pas le node) continue de les appliquer
    d["pins"] = st.get("pins") or {}
    d["pinned_layers"] = st.get("pinned") or []
    if st.get("trust") == "none" and st["stale"] is None:
        # aucun releve : on ne PEUT pas conclure (et on ne fait pas semblant)
        d["state"] = "no_record"
    elif st["consumed"] is None and st["latest"] is None:
        # 'n/a' (le shot ne lit pas ce(s) layer(s)) plutot que 'error' : les messages
        # viennent soit du releve ('absent du releve'), soit de l'import ('non consomme')
        benign = ("non consomme", "absent du releve", "aucun des layers suivis")
        d["state"] = (
            "no_layer"
            if (st["err"] and any(b in st["err"] for b in benign))
            else "error"
        )
    elif st["stale"] is None:
        # version non resolue : indecidable -> 'n/a', surtout pas 'up to date'
        d["state"] = "no_layer"
    elif st["stale"]:
        d["state"] = "outdated"
    elif st.get("pinned"):
        d["state"] = "pinned"  # en retard, mais epingle par l'artiste : pas perime
    else:
        d["state"] = "uptodate"
    return d


# --------------------------------------------------------------------------- #
#  Main
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(
        description="Re-cache headless de shots cfx (Prism/hython)"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="(optionnel) json de config ; sinon tout via les flags explicites",
    )
    parser.add_argument("--hip", default=None, help="chemin du .hip de la scene cfx")
    parser.add_argument(
        "--project", default=None, help="config projet Prism (pipeline.json)"
    )
    parser.add_argument("--stage-root", default=None, help="racine LOP (defaut /stage)")
    parser.add_argument(
        "--import-pattern", default=None, help="pattern nom node import (defaut {shot})"
    )
    parser.add_argument(
        "--cache-pattern",
        default=None,
        help="pattern nom node cache (defaut cache_{shot})",
    )
    parser.add_argument(
        "--import-node-type",
        default=None,
        help="type du node import (defaut prism::LOP_Import)",
    )
    parser.add_argument(
        "--import-path-parm",
        default=None,
        help="parm de chemin sur l'import (defaut filepath)",
    )
    parser.add_argument(
        "--tracked-layer",
        action="append",
        default=None,
        help="layer dont on suit la version (repetable : plusieurs layers suivis)",
    )
    parser.add_argument(
        "--tracked-mode",
        choices=("or", "and"),
        default="or",
        help="plusieurs layers : 'or' = perime si UN bouge, 'and' = si TOUS ont bouge",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="ne pas sauver la scene apres apply (defaut: version-up Prism)",
    )
    parser.add_argument(
        "--shots",
        nargs="*",
        default=None,
        help="items a traiter (id de node cache, ou nom de shot Prism)",
    )
    parser.add_argument(
        "--all", action="store_true", help="traiter tous les shots de la config"
    )
    parser.add_argument(
        "--apply", action="store_true", help="executer reellement (sinon dry-run)"
    )
    parser.add_argument("--force", action="store_true", help="re-cacher meme si a jour")
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="dump read-only de la structure des nodes cache (diagnostic HDA)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="sort l'etat des shots en JSON (read-only, pour l'UI)",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="decouvre les shots presents dans la scene (ignore la liste config)",
    )
    parser.add_argument(
        "--fx-plan",
        default=None,
        help="(FX) json {cache_id: [chemins caches SOP, ordonnes]} = quels caches SOP "
        "re-simuler par shot (coches dans l'UE). Absent -> toute la chaine decouverte.",
    )
    parser.add_argument(
        "--cache-plan",
        default=None,
        help="json {item_id: [chemins lop_filecache a executer]} = quels caches USD "
        "executer par item (coches dans l'UI). Absent -> tous. Une liste VIDE veut dire "
        "'aucun cache' (bump import + render seuls) : ce n'est PAS la meme chose qu'une "
        "entree absente.",
    )
    parser.add_argument(
        "--render-node-type",
        default=None,
        help="type du node render lighting (defaut prism::LOP_Render)",
    )
    parser.add_argument(
        "--render-plan",
        default=None,
        help="(Lighting) json {cache_id: [chemins LOP_Render a soumettre]} = quels "
        "renders soumettre a la ferme par shot (coches dans l'UI). Absent -> aucun.",
    )
    parser.add_argument(
        "--farm-plan",
        default=None,
        help="(Lighting) json {'*': {reglages ferme}} = overrides appliques a chaque render "
        "soumis (frames, priority, chunk, pool, group, machine_limit, suspended, "
        "high_prio...). Cle absente = valeur de la scene. Cf apply_farm_settings.",
    )
    # tolere un '--' de separation eventuel passe par hython
    argv = [a for a in sys.argv[1:] if a != "--"]
    args = parser.parse_args(argv)

    # cfg = defauts, puis (optionnel) json de config, puis override par les flags.
    cfg = dict(DEFAULTS)
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    overrides = {
        "project": args.project,
        "hip": args.hip,
        "stage_root": args.stage_root,
        "import_node_pattern": args.import_pattern,
        "cache_node_pattern": args.cache_pattern,
        "import_node_type": args.import_node_type,
        "render_node_type": args.render_node_type,
        "import_path_parm": args.import_path_parm,
        # --tracked-layer est repetable -> liste ; on garde aussi la forme simple pour
        # tout ce qui n'a besoin que d'UN nom (messages, cle de repli).
        "tracked_layer": (args.tracked_layer or [None])[0],
        "tracked_layers": args.tracked_layer,
        "tracked_mode": args.tracked_mode,
    }
    for k, v in overrides.items():
        if v:
            cfg[k] = v
    if not cfg.get("hip") or not cfg.get("project"):
        log("ERREUR: il faut au minimum --hip et --project (ou un --config complet).")
        sys.exit(2)
    # plan FX (quels caches SOP re-simuler par shot) : fichier json optionnel
    if args.fx_plan:
        try:
            with open(args.fx_plan, "r", encoding="utf-8") as f:
                cfg["fx_plan"] = json.load(f)
        except Exception as e:
            log("fx-plan illisible (%s) -> chaine complete par defaut" % e)
    # plan CACHE (quels lop_filecache executer par item) : json optionnel
    if args.cache_plan:
        try:
            with open(args.cache_plan, "r", encoding="utf-8") as f:
                cfg["cache_plan"] = json.load(f)
        except Exception as e:
            log("cache-plan illisible (%s) -> tous les caches par defaut" % e)
    # plan RENDER (quels LOP_Render soumettre a la ferme par shot) : json optionnel
    if args.render_plan:
        try:
            with open(args.render_plan, "r", encoding="utf-8") as f:
                cfg["render_plan"] = json.load(f)
        except Exception as e:
            log("render-plan illisible (%s) -> aucun render soumis" % e)
    # reglages ferme : json optionnel. Illisible = on ne soumet PAS avec d'autres
    # reglages que ceux demandes -> on vide le render-plan.
    if args.farm_plan:
        try:
            with open(args.farm_plan, "r", encoding="utf-8") as f:
                cfg["farm_plan"] = json.load(f)
        except Exception as e:
            log("farm-plan illisible (%s) -> AUCUN render soumis" % e)
            cfg["render_plan"] = {}
    # commentaire des renders soumis. Scene NON sauvee -> on le DIT dans le render : son
    # sourceScene pointera une scene qui ne contient pas l'update (l'image, elle, est
    # juste : le submitter exporte l'USD depuis la session vivante).
    cfg["render_comment"] = cfg.get("save_comment", "auto update - lop_update_cache")
    if args.no_save:
        cfg["render_comment"] += " (scene not saved)"

    import hou

    # Filet de securite : verifier que hou vient bien de la version epinglee (HFS de l'env)
    # -> transforme une collision multi-versions en erreur CLAIRE (au lieu d'un segfault
    # silencieux comme quand un env 21.0.729 pollue un hython 21.0.596).
    want_hfs = os.environ.get("HFS", "")
    try:
        got_hfs = hou.text.expandString("$HFS")  # H21 : hou.expandString est deprecie
    except AttributeError:
        got_hfs = hou.expandString("$HFS")
    log("Houdini: %s  (HFS=%s)" % (hou.applicationVersionString(), got_hfs))

    def _build_of(p):
        base = os.path.basename(os.path.normpath(p)) if p else ""
        nums = re.findall(r"\d+", base)
        return nums[-1] if nums else ""

    wb, gb = _build_of(want_hfs), _build_of(got_hfs)
    if wb and gb and wb != gb:
        raise RuntimeError(
            "Collision de version Houdini : l'env epingle HFS=%s (build %s) mais hou "
            "s'execute depuis %s (build %s). Lance le hython de la MEME version que "
            "l'environnement, ou nettoie PATH/PYTHONPATH/HOUDINI_PATH."
            % (want_hfs, wb, got_hfs, gb)
        )

    mode = "STATUS" if args.status else ("APPLY" if args.apply else "DRY-RUN")
    log("=" * 70)
    log("recache_cfx v%s" % VERSION)
    log("Scene  : %s" % cfg["hip"])
    log("Mode   : %s%s" % (mode, "  (+force)" if args.force else ""))

    pcore = bootstrap_prism()
    log(
        "Prism  : %s  (uiAvailable=%s)"
        % (getattr(pcore, "version", "?"), getattr(pcore, "uiAvailable", "?"))
    )
    ensure_project(pcore, cfg["project"])

    hip = cfg["hip"]
    # Releves des caches precedents (sidecar partage a cote du hip) : c'est eux qui
    # portent la peremption, pas l'etat de la scene (cf preview.record_state).
    side = preview.load_sidecar(hip)
    cfg["cache_records"] = side.get("cached") or {}
    if cfg["cache_records"]:
        log("Releves de cache : %d shot(s) connus" % len(cfg["cache_records"]))
    else:
        log(
            "Aucun releve de cache pour cette scene (sidecar vierge) : la peremption "
            "sera indeterminee tant qu'un cache n'aura pas ete lance par l'outil."
        )

    log("Ouverture scene : %s" % hip)
    _t = time.perf_counter()
    hou.hipFile.load(hip, suppress_save_prompt=True, ignore_load_warnings=True)
    log("Scene chargee (%s)." % _span(_t))

    # appariement par TOPOLOGIE (cache -> import), independant des noms de node
    all_items = discover_pairs(hou, pcore, cfg)
    items = all_items
    if args.shots:
        sel = set(args.shots)

        def _match(it):
            imp = it["import"]
            return (
                it["id"] in sel
                or it["shot"] in sel
                or (imp is not None and imp.name() in sel)
            )

        items = [it for it in items if _match(it)]
    log("Items  : %d" % len(items))
    if not items:
        # Dire POURQUOI c'est vide : sans ca, l'UI affichait juste une table vide (ou
        # pire, les lignes de la scene precedente). Ex vecu : une scene 'Confo' qui n'a
        # que des LOP_Render et aucun lop_filecache -> l'outil s'ancre sur les caches,
        # donc il ne voit rien. /!\ Distinguer "la scene n'a rien" de "le filtre --shots
        # n'a rien matche" : sinon on annonce "aucun node de cache" alors que la scene en
        # a, et on envoie l'utilisateur sur une fausse piste.
        if all_items:
            log(
                "Aucun item ne correspond a --shots %s. Ids disponibles : %s"
                % (
                    " ".join(args.shots or []),
                    ", ".join("%s (%s)" % (it["id"], it["shot"]) for it in all_items),
                )
            )
        else:
            n_ren = len(collect_renders(hou, cfg))
            n_imp = len(collect_imports(hou, pcore, cfg))
            log(
                "Rien a traiter : aucun node de cache (%s) NI de render (%s) exploitable."
                % (
                    cfg.get("cache_node_type", "prism::lop_filecache"),
                    cfg.get("render_node_type", "prism::LOP_Render"),
                )
            )
            log("  imports trouves : %d   |   renders trouves : %d" % (n_imp, n_ren))
        sys.exit(2)

    # --- mode STATUS : JSON pour l'UI (read-only) ---
    if args.status:
        data = [status_item(hou, pcore, it, cfg) for it in items]
        print(">>>STATUS_JSON>>>")
        print(json.dumps(data, indent=2))
        print("<<<STATUS_JSON<<<")
        sys.exit(0)

    if args.inspect:
        for it in items:
            if it["import"] is not None:
                inspect_node(hou, it["import"], "IMPORT %s" % it["id"])
            inspect_node(hou, it["cache"], "CACHE %s" % it["id"])
        sys.exit(0)

    if args.apply:
        # aucune fenetre modale ne doit geler hython (sanity_check studio du hook
        # prePublish, popups Prism...) : reponse automatique comme en GUI, logguee
        headless_guard.install(log)

    reports = []
    for i, it in enumerate(items):
        if args.apply:
            # marqueur de progression pour la barre de l'UI
            print(">>>PROGRESS>>>%d/%d<<<" % (i + 1, len(items)), flush=True)
        try:
            reports.append(process_item(hou, pcore, it, cfg, args.apply, args.force))
        except Exception as e:
            import traceback

            log(
                "ITEM %s -> EXCEPTION NON GEREE:\n%s"
                % (it["id"], traceback.format_exc())
            )
            reports.append(
                {
                    "id": it["id"],
                    "shot": it["shot"],
                    "ok": False,
                    "msg": "exception: %s" % e,
                }
            )

    # --- releves de cache -> l'UI les ecrit dans le sidecar (un seul ecrivain) ------
    if args.apply:
        recs = harvest_records(items, reports, cfg)
        if recs:
            print(">>>CACHE_RECORDS>>>")
            print(json.dumps(recs, indent=2))
            print("<<<CACHE_RECORDS<<<")

    # --- lighting : ecrire l'etat Enabled des executions AVANT le save (behavior 2) ---
    if args.apply and (cfg.get("render_plan") or {}):
        apply_render_selections(hou, items, reports, cfg)

    # --- save du batch : une seule fois, version-up Prism avec commentaire ---
    n_applied = sum(1 for r in reports if r.get("applied"))
    if args.apply and n_applied and not args.no_save:
        try:
            _t = time.perf_counter()
            pcore.saveScene(
                versionUp=True,
                comment=cfg.get("save_comment", "auto update - lop_update_cache"),
            )
            newscene = (pcore.getCurrentFileName() or "").replace("\\", "/")
            log(
                "Scene sauvee (version-up Prism, %d shot(s), %s): %s"
                % (n_applied, _span(_t), newscene)
            )
            print(">>>SAVED_SCENE>>>%s<<<SAVED_SCENE<<<" % newscene)
        except Exception:
            import traceback

            log(
                "SAVE KO (les caches sont ecrits quand meme):\n%s"
                % traceback.format_exc()
            )
    elif args.apply and n_applied:
        # choix EXPLICITE de l'utilisateur ("Leave untouched") : on ne cree pas de
        # version dans la chaine d'un autre (un lighter qui sauve par-dessus sa vNNN
        # tomberait le lendemain sur NOTRE vNNN+1, sans son travail).
        log("Scene NON sauvee (choix 'Leave untouched') : caches publies, .hip intact.")

    # --- submit renders (lighting) : APRES le save -> la ferme rend la scene bumpee ---
    if args.apply and (cfg.get("render_plan") or {}):
        try:
            submit_renders(hou, pcore, items, reports, cfg)
        except Exception:
            import traceback

            log("SUBMIT RENDERS KO:\n%s" % traceback.format_exc())

    # resume final
    log("=" * 70)
    log("RESUME (%s):" % mode)
    for r in reports:
        flag = "LOCK" if r.get("skipped_locked") else ("OK " if r.get("ok") else "KO ")
        log("  %s %-14s %s" % (flag, r.get("id", "?"), r.get("msg", "")))
    n_locked = sum(1 for r in reports if r.get("skipped_locked"))
    if n_locked:
        log(
            "  ! %d shot(s) FX non re-simules (HDA locked) -> re-sim manuel dans Houdini"
            % n_locked
        )

    # apply : re-emet l'etat frais de TOUS les items (pas juste la selection) pour
    # que l'UI garde la liste complete avec les etats a jour.
    # /!\ COUTEUX : c'est un getLatestVersionFromPath (reseau) + une ouverture USD PAR
    # shot de la scene (20 sur le CFX MASTER). Sans les logs ci-dessous, l'UI restait
    # bloquee sur "Wrapping up..." sans rien dire pendant tout ce temps.
    # Les caches sont DEJA publies et la scene DEJA sauvee a ce stade : interrompre ici
    # ne fait perdre que le rafraichissement du tableau.
    if args.apply:
        _t = time.perf_counter()
        log("Rafraichissement de l'etat des %d shot(s) de la scene..." % len(all_items))
        data = []
        for i, it in enumerate(all_items):
            print(">>>PROGRESS>>>%d/%d<<<" % (i + 1, len(all_items)), flush=True)
            data.append(status_item(hou, pcore, it, cfg))
        log("Etat rafraichi (%s)." % _span(_t))
        print(">>>STATUS_JSON>>>")
        print(json.dumps(data, indent=2))
        print("<<<STATUS_JSON<<<")

    log("Total : %.1fs (de l'import a la fin)" % (time.perf_counter() - _START))
    n_ko = sum(0 if r.get("ok") else 1 for r in reports)
    sys.exit(1 if n_ko else 0)


if __name__ == "__main__":
    main()
