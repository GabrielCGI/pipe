# -*- coding: utf-8 -*-
r"""
maya_refs.py - Lecture des references d'une scene Maya SANS ouvrir Maya.

Meme idee que preview.py pour l'USD : un `.ma` est de l'ASCII, et ses directives
`file -r` sont EN TETE du fichier. Lire les premiers ko d'une scene de 125 Mo suffit
donc a savoir quels rigs elle reference et dans quelle version -> detection instantanee,
sans licence, sans Maya.

Les references de rig suivent EXACTEMENT le layout produit Prism des USD :
    <projet>/03_Production/Assets/<cat>/<asset>/Export/Rigging/vNNN/<asset>_Rigging_vNNN.mb
-> `preview.split_product` / `preview.latest_product_version` les traitent tels quels.
On ne duplique donc AUCUNE logique de version ici.

/!\ Pieges verifies sur yuka_2604 :
  - le CHEMIN est sur la ligne SUIVANTE de la directive `file -r` (le .ma passe a la
    ligne apres les options) -> il faut parser le bloc jusqu'au `;`, pas la ligne ;
  - Maya ecrit un DOUBLE SLASH apres la racine du projet ('I:/yuka_2604//03_Production')
    -> normaliser avant tout glob ;
  - un meme rig est reference N fois (14 namespaces `baitedHook_Rigging*` dans une seule
    scene) -> raisonner par ASSET, jamais par reference ;
  - une scene `.mb` est binaire : illisible ici (il faudrait mayapy).

Les STATES Prism (exports compris) sont eux aussi en tete du .ma, dans
`fileInfo "PrismStates" "<json echappe MEL>"` -> la liste des exports d'une scene se lit
sans Maya elle aussi (cf scene_exports).
"""

import json
import os
import re

from . import preview

# `file -r <options...> "<chemin>";`  -- le chemin peut etre sur une autre ligne, donc on
# parse jusqu'au point-virgule. `-rdi 1` (deferred) est une PRE-declaration : on ne garde
# que les vraies directives `file -r`, sinon chaque reference sort en double.
_REF_RE = re.compile(
    r'file\s+-r\s+(?P<opts>(?:(?!\bfile\s+-r)[^;])*?)"(?P<path>[A-Za-z]:/[^"]+\.(?:ma|mb))"\s*;',
    re.S,
)
_NS_RE = re.compile(r'-ns\s+"([^"]+)"')
_RFN_RE = re.compile(r'-rfn\s+"([^"]+)"')

HEAD_BYTES = 400000  # les `file -r` tiennent tres largement dedans


def is_ascii_maya(path):
    """True si `path` est un .ma ASCII (magic '//Maya ASCII'). On teste le CONTENU, pas
    l'extension : un .mb renomme, ou un .ma tronque, ne doit pas etre parse a l'aveugle."""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
    except Exception:
        return False
    return head.lstrip(b"\xef\xbb\xbf").startswith(b"//Maya ASCII")


def read_head(path, size=HEAD_BYTES):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(size)
    except Exception:
        return ""


def scene_references(scene):
    """[{ns, refnode, path, asset, product, version}] des references de `scene`.

    Retourne [] si la scene n'est pas de l'ASCII lisible -- on ne conclut JAMAIS sur un
    fichier qu'on n'a pas su lire (cf la regle binaire/USD de preview.py)."""
    if not is_ascii_maya(scene):
        return []
    head = read_head(scene)
    out = []
    for m in _REF_RE.finditer(head):
        path = m.group("path").replace("//", "/")
        _root, product, version = preview.split_product(path)
        ns = _NS_RE.search(m.group("opts"))
        rfn = _RFN_RE.search(m.group("opts"))
        out.append(
            {
                "ns": ns.group(1) if ns else "",
                "refnode": rfn.group(1) if rfn else "",
                "path": path,
                "asset": asset_of(path),
                "product": product,
                "version": version,
            }
        )
    return out


def asset_of(path):
    """'Characters/fishAncient' depuis un chemin de produit d'asset. '' si hors Assets."""
    p = (path or "").replace("\\", "/")
    if "/Assets/" not in p or "/Export/" not in p:
        return ""
    return p.split("/Assets/", 1)[1].split("/Export/", 1)[0]


def export_dir_of(path):
    """Le dossier .../Export d'un chemin de produit. '' si la forme ne colle pas."""
    p = (path or "").replace("\\", "/")
    return (p.split("/Export/", 1)[0] + "/Export") if "/Export/" in p else ""


def latest_for(ref):
    """Derniere version publiee du produit de cette reference (int), ou None."""
    export = export_dir_of(ref.get("path"))
    prod = ref.get("product")
    if not export or not prod:
        return None
    return preview.latest_product_version(export, prod)


def group_by_asset(refs):
    """{(asset, produit): {refs, version, latest, stale, paths}} -- l'unite de decision
    est l'ASSET : un rig est souvent reference des dizaines de fois, on ne va pas
    demander a l'artiste de cocher 14 namespaces pour un seul hameçon."""
    groups = {}
    for r in refs:
        key = (r["asset"], r["product"])
        g = groups.setdefault(
            key,
            {
                "asset": r["asset"],
                "product": r["product"],
                "refs": [],
                "version": r["version"],
                "latest": None,
                "stale": False,
            },
        )
        g["refs"].append(r)
        # la version du groupe = la PLUS ANCIENNE des references (c'est elle qui decide
        # de la peremption ; des refs du meme rig peuvent diverger)
        if r["version"] >= 0 and (g["version"] < 0 or r["version"] < g["version"]):
            g["version"] = r["version"]
    for g in groups.values():
        g["latest"] = latest_for(g["refs"][0])
        g["stale"] = bool(
            g["latest"] is not None and g["version"] >= 0 and g["latest"] > g["version"]
        )
    return groups


def rig_status(scene):
    """[{id, asset, product, version, latest, stale, state, refs, n_refs}] : un item par
    ASSET reference (l'unite que l'artiste coche). Sans Maya.

    Les references qui ne sont pas des produits Prism (chemin hors .../Export/<produit>/
    vNNN/) sont ignorees : on ne sait pas dire si elles sont a jour, et une ligne
    "version ?" n'aiderait personne a decider."""
    refs = [r for r in scene_references(scene) if r.get("product")]
    out = []
    for (asset, product), g in sorted(group_by_asset(refs).items()):
        # version referencee SUPPRIMEE du disque (menage des vieux rigs) : la scene s'ouvre
        # avec une reference vide -> le swap vers la derniere est justement la reparation
        missing = sorted(
            {r["path"] for r in g["refs"] if not os.path.isfile(r["path"])}
        )
        out.append(
            {
                "id": "%s|%s" % (asset, product),
                "asset": asset,
                "product": product,
                "version": ("v%03d" % g["version"]) if g["version"] >= 0 else None,
                "latest": ("v%03d" % g["latest"]) if g["latest"] is not None else None,
                "stale": g["stale"],
                "missing": missing,
                "state": "outdated" if g["stale"] else "uptodate",
                "refs": [
                    {"ns": r["ns"], "refnode": r["refnode"], "path": r["path"]}
                    for r in g["refs"]
                ],
                "n_refs": len(g["refs"]),
            }
        )
    return out


# --------------------------------------------------------------------------- #
#  States Prism (exports) : lus dans le fileInfo "PrismStates" du .ma, sans Maya
# --------------------------------------------------------------------------- #
# Classes de state qui PUBLIENT un produit. Le Playblast est exclu : il lui faut un
# viewport, qu'un mayapy headless n'a pas (captureViewportThumbnail plante deja au save).
EXPORT_CLASSES = ("USD Export", "Export")
STATES_BYTES = 1500000  # le fileInfo suit les `file -r` : tres en tete du fichier
_STATES_TAG = 'fileInfo "PrismStates" "'
_MEL_ESC = {"n": "\n", "t": "\t", "r": "\r"}


def _mel_string_at(text, start):
    """Contenu (encore echappe) de la chaine MEL qui commence a `start`, ou None si elle
    n'est pas fermee dans `text` (tete de fichier tronquee)."""
    i = start
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == '"':
            return text[start:i]
        i += 1
    return None


def scene_states(scene):
    """Les states Prism de la scene, dans l'ordre du State Manager. [] si la scene n'en a
    pas ou n'est pas lisible : on ne fabrique jamais une liste qu'on n'a pas su lire."""
    if not is_ascii_maya(scene):
        return []
    for size in (STATES_BYTES, 8 * STATES_BYTES):
        head = read_head(scene, size)
        at = head.find(_STATES_TAG)
        if at < 0:
            return []
        raw = _mel_string_at(head, at + len(_STATES_TAG))
        if raw is not None:
            break
    else:
        return []
    text = re.sub(
        r"\\(.)", lambda m: _MEL_ESC.get(m.group(1), m.group(1)), raw, flags=re.S
    )
    try:
        data = json.loads(text)
    except Exception:
        return []
    states = data.get("states") if isinstance(data, dict) else None
    return [s for s in (states or []) if isinstance(s, dict)]


def export_product(state):
    """Produit publie par un state d'export ('' si on ne sait pas le dire).

    Regles verifiees sur SH0125 (yuka_2604) contre `state.ui.getProductname()` du State
    Manager : Layer + sublayer -> `_layer_<dep>_<sublayer>` ; Custom -> champ `product` ;
    Export Prism classique -> `productname`. Le reste retombe sur le dernier export."""
    if state.get("stateclass") == "Export":
        return state.get("productname") or ""
    if state.get("saveMode") == "Custom" and state.get("product"):
        return state["product"]
    dep, sub = state.get("departmentLayer"), state.get("sublayer")
    if state.get("saveMode") == "Layer" and dep and state.get("useSublayer") and sub:
        return "_layer_%s_%s" % (dep, sub)
    last = state.get("lastexportpath") or ""
    return preview.split_product(last)[1] if last and last != "None" else ""


def entity_export_dir(scene):
    """.../<entite>/Export d'une scene rangee en .../<entite>/Scenefiles/<dept>/<task>/."""
    p = (scene or "").replace("\\", "/")
    return (p.split("/Scenefiles/", 1)[0] + "/Export") if "/Scenefiles/" in p else ""


def scene_exports(scene):
    """[{uuid, name, stateclass, product, enabled, output_type, latest}] des states
    d'export de la scene, dans l'ordre du State Manager.
    enabled = coche dans le State Manager de la scene (c'est le defaut propose).
    latest  = derniere version publiee de ce produit pour l'entite de la scene."""
    export_dir = entity_export_dir(scene)
    out = []
    for st in scene_states(scene):
        cls = st.get("stateclass")
        if cls not in EXPORT_CLASSES or not st.get("uuid"):
            continue
        product = export_product(st)
        latest = (
            preview.latest_product_version(export_dir, product)
            if export_dir and product
            else None
        )
        out.append(
            {
                "uuid": st["uuid"],
                "name": st.get("statename") or st.get("stateName") or cls,
                "stateclass": cls,
                "product": product,
                "enabled": st.get("stateenabled") == 2,
                "output_type": st.get("outputtype") or st.get("curoutputtype") or "",
                "latest": ("v%03d" % latest) if latest is not None else None,
            }
        )
    return out


def target_path(ref, version):
    """Chemin de la reference amenee a `version` : on remplace le token de version DANS
    le dossier ET dans le nom de fichier (Prism les repete tous les deux).
    None si le fichier cible n'existe pas -- on ne fabrique pas un chemin qui n'existe
    pas, on prefere ne rien faire et le dire."""
    p = (ref.get("path") or "").replace("\\", "/")
    old = ref.get("version")
    if not p or old is None or old < 0 or version is None:
        return None
    new = re.sub(r"v%03d" % old, "v%03d" % version, p)
    if new == p or not os.path.isfile(new):
        # le nom du fichier publie peut differer : on cherche dans le dossier de version
        export, prod = export_dir_of(p), ref.get("product")
        vdir = os.path.join(export, prod or "", "v%03d" % version)
        if os.path.isdir(vdir):
            ext = os.path.splitext(p)[1].lower()
            cands = [
                f
                for f in sorted(os.listdir(vdir))
                if f.lower().endswith((".ma", ".mb"))
            ]
            same = [f for f in cands if f.lower().endswith(ext)]
            if same or cands:
                return os.path.join(vdir, (same or cands)[0]).replace("\\", "/")
        return None
    return new
