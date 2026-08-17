# -*- coding: utf-8 -*-
"""
preview.py - Detection de peremption SANS Houdini (pur Python : filesystem + texte).

Idee : un container shot USD est un .usda ASCII dont les subLayers pointent des
versions precises de chaque layer master (.../_layer_anm_master/v010/...). Donc :
  - version CONSOMMEE  = celle du container que la scene pointe (snapshot du dernier
    passage par l'app, ou re-parse du meme fichier).
  - version LATEST     = celle du dernier container sur disque (glob des vNNN).
Comparer les deux par layer = meme resultat que le moteur hython, mais instantane et
sans charger Houdini. Le moteur hython reste la verite terrain (Load Scene).

/!\ La regle "un container est toujours .usda ASCII" est VIOLEE en pratique : des
containers crate binaires existent sur yuka_2604 (MASTER/MT0020/Export/USD/v008, magic
'PXR-USDC'), et 144 produits sur 441 ont un latest binaire. Le preview ne sait lire que
l'ASCII -> il DOIT tester is_ascii_usd() et refuser de conclure sinon (preview=False),
au lieu de prendre "je n'ai rien lu" pour "rien n'a bouge". pxr.Sdf (moteur) lit les
deux : le moteur reste la verite terrain, le preview n'est qu'un raccourci.

AGNOSTIQUE au layer importe : une scene peut aussi importer DIRECTEMENT un layer
master (.../_layer_anm_master/v012/...) au lieu du container du shot. On ajoute donc
TOUJOURS aux subLayers le produit que le chemin designe lui-meme, a sa version
(v012) -> le layer tracke est trouve dans les deux cas. Attention : un layer master
n'est PAS une feuille, il sublayer ses _class/_main -> on fusionne, on ne devine pas.
"""

import os
import re
import json
import glob

_SUBLAYER_RE = re.compile(r"([^/@]+)/v(\d+)/")  # idem recache_cfx : parite obligatoire
_SUBLAYER_OPEN_RE = re.compile(r"subLayers\s*=\s*\[")
_VDIR_RE = re.compile(r"[/\\]v(\d+)$")
_PRODUCT_RE = re.compile(r"([^/\\]+)[/\\]v(\d+)[/\\][^/\\]+$")
_HIP_VER_RE = re.compile(r"_v(\d+)\.hip", re.IGNORECASE)


def _head(path, size=131072):
    """Debut d'un fichier texte, '' si illisible/absent."""
    if not path or not os.path.isfile(path):
        return ""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(size)
    except Exception:
        return ""


def parse_container_layers(usda_path):
    """{nom_layer: version_int} depuis le bloc subLayers d'un container .usda (texte).
    On se limite STRICTEMENT au bloc `subLayers = [...]` (en tete du fichier) : sinon
    on ramasserait aussi les references/payloads versionnes, que le moteur ignore
    (pxr.Sdf ne lit que subLayerPaths) -> preview et moteur divergeraient.
    {} si le fichier n'a pas de subLayers (ou s'il est binaire/illisible)."""
    head = _head(usda_path)
    m = _SUBLAYER_OPEN_RE.search(head)
    if not m:
        return {}
    rest = head[m.end() :]
    end = rest.find("]")
    block = rest if end < 0 else rest[:end]  # head tronque -> on parse ce qu'on a
    # un subLayer peut etre relatif (@../../x/v001/y.usda@) OU absolu Windows
    # (@I:\proj\...\v001\y.usdc@) -> normaliser, sinon on rate les seconds (le moteur,
    # lui, normalise depuis toujours -> on divergerait).
    block = block.replace("\\", "/")
    out = {}
    for name, v in _SUBLAYER_RE.findall(block):
        vi = int(v)
        if name not in out or vi > out[name]:
            out[name] = vi
    return out


def split_product(path):
    """(dossier_produit, nom_produit, version) d'un chemin de produit Prism
    .../Export/<produit>/vNNN/<fichier>. ('', '', -1) si la forme ne colle pas."""
    m = _PRODUCT_RE.search((path or "").replace("\\", "/"))
    if not m:
        return "", "", -1
    return os.path.dirname(os.path.dirname(path)), m.group(1), int(m.group(2))


def product_layers(path):
    """{produit: version} du produit Prism que `path` DESIGNE lui-meme
    (.../Export/<produit>/vNNN/<fichier>). {} si le chemin n'a pas cette forme."""
    _root, name, v = split_product(path)
    return {name: v} if name and v >= 0 else {}


def path_layers(path):
    """{layer: version} de TOUT ce que consomme `path` : ses subLayers + le produit
    qu'il designe lui-meme (qui prime). Rend la detection agnostique a la granularite
    de l'import : container du shot OU layer master direct.
    Pendant pur-Python de recache_cfx.stack_layers -> les deux DOIVENT rester d'accord
    (cf test de parite en hython) -- MAIS seulement sur de l'ASCII : sur un crate
    binaire les subLayers manquent ici alors que pxr.Sdf les voit. D'ou le garde-fou
    is_ascii_usd() en amont dans refresh_entry : ne JAMAIS conclure sur du binaire."""
    out = parse_container_layers(path)
    out.update(product_layers(path))
    return out


def is_ascii_usd(path):
    """True si `path` est un USD ASCII (donc parsable en texte). On teste le CONTENU
    (magic '#usda'), PAS l'extension : sur yuka_2604 des containers sont publies en
    crate binaire malgre la regle (ex MASTER/MT0020/Export/USD/v008/*.usdc, magic
    'PXR-USDC'). pxr.Sdf (moteur) lit les deux ; le preview, lui, ne lit que l'ASCII."""
    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except Exception:
        return False
    return head.lstrip(b"\xef\xbb\xbf").startswith(b"#usda")


_USD_EXT = (".usda", ".usdc", ".usd", ".usdz")


def _usd_files(vdir):
    """Fichiers USD d'un dossier de version, le .usda d'abord (seul lisible en texte).
    Filtre par EXTENSION EXACTE, jamais par glob '*.usd*' : les dossiers de version
    contiennent aussi des sauvegardes 'x.usda.20260610_112408.bak' (vues en vrai sur
    yuka_2604) qu'un tel glob attrape -- et qui trient meme AVANT le vrai 'x.usdc'."""
    files = [
        f
        for f in glob.glob(os.path.join(vdir, "*"))
        if os.path.splitext(f)[1].lower() in _USD_EXT
    ]
    files.sort(key=lambda f: (os.path.splitext(f)[1].lower() != ".usda", f))
    return files


def latest_product(import_path):
    """(fichier, version) de la DERNIERE version du produit Prism de `import_path`
    (container USD comme layer master). ('', -1) si introuvable.

    La version vient du NOM DU DOSSIER : fiable meme si le fichier est binaire. Le
    fichier renvoye est le .usda de cette version si elle en a un, sinon son premier
    usd (potentiellement binaire) -> l'appelant DOIT tester is_ascii_usd() avant de
    parser. On ne saute PAS une version binaire pour retomber sur une ASCII plus
    vieille : ce serait mentir sur la derniere version publiee.
    Une version sans aucun fichier usd est ignoree (publish avorte)."""
    root, _name, _v = split_product(import_path)
    if not root:
        return "", -1
    best_v, best_path = -1, ""
    for d in glob.glob(os.path.join(root, "v*")):
        m = _VDIR_RE.search(d)
        if not m:
            continue
        v = int(m.group(1))
        if v <= best_v:
            continue
        files = _usd_files(d)
        if files:
            best_v, best_path = v, files[0]
    return best_path, best_v


def _vlabel(v):
    return ("v%03d" % v) if v is not None and v >= 0 else None


def refresh_entry(entry):
    """Met a jour entry['layers'] (consommee vs derniere sur disque) + stack_consumed/
    stack_latest, PAR LECTURE DISQUE. AGNOSTIQUE a ce que l'import pointe : container
    de shot (le layer sort des subLayers) OU layer master direct (il sort du chemin du
    produit importe, cf path_layers). L'etat par layer est recalcule cote
    UI depuis 'layers' (comme pour le moteur). Retourne entry.
    entry['import_path'] = ce que la scene pointe. Pose entry['preview']=True/False.

    REGLE DE SURETE : le preview ne REPEINT le snapshot que s'il a pu TOUT lire. Un USD
    binaire (crate) est illisible en texte -> ses subLayers ressortiraient a {}, le
    layer tracke aurait latest=None -> stale=False -> FAUX 'up to date', et on
    ecraserait un 'outdated' correct calcule par le moteur. Dans ce cas on sort en
    preview=False : on garde le snapshot moteur, le shot perd juste le scan rapide."""
    imp = entry.get("import_path")
    if not imp or not os.path.isfile(imp):
        entry["preview"] = (
            False  # pas de source disque -> on garde le snapshot tel quel
        )
        return entry
    latest_path, latest_v = latest_product(imp)
    if latest_v < 0 or not latest_path:
        entry["preview"] = False  # produit introuvable sur disque -> on ne conclut pas
        return entry
    if not is_ascii_usd(imp) or not is_ascii_usd(latest_path):
        entry["preview"] = False  # binaire : seul le moteur (pxr.Sdf) sait lire
        return entry
    consumed = path_layers(imp)
    latest = path_layers(latest_path)
    layers = {}
    for name in set(consumed) | set(latest):
        c, lv = consumed.get(name), latest.get(name)
        layers[name] = {
            "consumed": _vlabel(c),
            "latest": _vlabel(lv),
            "stale": bool(c is not None and lv is not None and lv > c),
        }
    entry["layers"] = layers
    m = _VDIR_RE.search(os.path.dirname(imp))
    entry["stack_consumed"] = (
        _vlabel(int(m.group(1))) if m else entry.get("stack_consumed")
    )
    entry["stack_latest"] = _vlabel(latest_v)
    entry["preview"] = True
    return entry


def refresh_status(status, records=None):
    """Rafraichit tous les shots depuis le disque (aucun Houdini). Modifie et retourne
    la liste. C'est le 'scan en arriere-plan'.

    `records` = releves de cache par shot (sidecar). Quand un shot en a un, il PRIME :
    c'est la seule methode qui marche avec usd_layer_stack (qui se resout toujours au
    dernier publish, donc l'etat de la scene ne dit rien de la peremption)."""
    records = records or {}
    for e in status or []:
        try:
            rec = records.get(e.get("shot"))
            if rec:
                refresh_entry_from_record(e, rec)
            else:
                refresh_entry(e)
        except Exception:
            e["preview"] = False
    return status


def refresh_entry_from_record(entry, record):
    """Etat d'un shot depuis son releve de cache (source de verite) : pour chaque layer
    releve, version consommee au cache vs derniere publiee sur disque."""
    export = record.get("export") or ""
    layers = {}
    for name, v in (record.get("layers") or {}).items():
        lv = latest_product_version(export, name)
        layers[name] = {
            "consumed": _vlabel(v),
            "latest": _vlabel(lv),
            "stale": bool(lv is not None and lv > v),
        }
    entry["layers"] = layers
    prod = record.get("product")
    pv_rec, pv_now = (
        record.get("product_version"),
        (latest_product_version(export, prod) if prod else None),
    )
    entry["stack_consumed"] = _vlabel(pv_rec)
    entry["stack_latest"] = _vlabel(pv_now)
    # publie hors outil -> le releve n'est plus garanti : on le SIGNALE
    entry["record_trust"] = (
        "uncertain"
        if (pv_rec is not None and pv_now is not None and pv_now > pv_rec)
        else "verified"
    )
    entry["preview"] = True
    return entry


# --------------------------------------------------------------------------- #
#  Peremption par RELEVE DE CACHE (source de verite, agnostique au node d'import)
#
#  On ne demande plus a la scene "quelle version pointes-tu ?" : ca ne marche que si le
#  node EPINGLE une version. Le node maison illogic::usd_layer_stack, lui, se resout
#  toujours au dernier publish (OnLoaded -> update()), donc apres un load il est
#  toujours "a jour" par construction -> la question n'a plus de sens.
#
#  A la place, AU MOMENT DU CACHE on releve ce qui a reellement ete consomme, et on
#  compare ce releve au disque. Marche pour les deux generations de node.
#
#  Releve (par shot, dans le sidecar) :
#     {"layers": {"_layer_anm_master": 12, ...},   # consomme au moment du cache
#      "product": "_layer_cfx_master",             # ce que le cache a publie
#      "product_version": 11,                      # sa version -> detecte un cache
#      "at": <timestamp>}                          #    fait HORS outil
# --------------------------------------------------------------------------- #
def scene_key(hip_path):
    """Cle de scene = basename sans extension NI version (SQ..._CFX_v071.hip ->
    SQ..._CFX) : le sidecar suit les version-ups."""
    base = os.path.splitext(os.path.basename(hip_path or ""))[0]
    return re.sub(r"_v\d+", "", base) or base


def sidecar_path(hip_path):
    """Le json partage a cote du hip. '' si le dossier n'existe pas. UNE seule
    definition, utilisee par l'UI ET par le moteur -> ils ne peuvent pas diverger."""
    d = os.path.dirname(hip_path or "")
    if not d or not os.path.isdir(d):
        return ""
    return os.path.join(d, scene_key(hip_path) + ".lopcache.json")


def load_sidecar(hip_path):
    """Contenu du sidecar (dict), {} si absent/illisible. Lecture seule."""
    p = sidecar_path(hip_path)
    if not p or not os.path.isfile(p):
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def export_dir_of(usd_path):
    """Le dossier .../Export a partir d'un chemin de produit. '' si introuvable."""
    p = (usd_path or "").replace("\\", "/")
    i = p.rfind("/Export/")
    return p[: i + len("/Export")] if i >= 0 else ""


def latest_product_version(export_dir, product):
    """Derniere version publiee d'un produit (int), ou None. La version vient du NOM du
    dossier -> fiable meme si le fichier est binaire."""
    best = None
    for d in glob.glob(os.path.join(export_dir or "", product, "v*")):
        m = re.match(r"^v(\d+)$", os.path.basename(d))
        if m and os.path.isdir(d):
            v = int(m.group(1))
            best = v if best is None or v > best else best
    return best


def record_state(export_dir, record, tracked):
    """Etat d'un shot depuis son releve de cache. Retourne
    {consumed, latest, stale, trust, err} :
      trust='verified'  -> le produit publie est bien celui qu'on a fait : releve fiable
      trust='uncertain' -> quelqu'un a re-publie depuis (cache hors outil) : on ne peut
                           plus affirmer avec quoi ; on le DIT au lieu de mentir
      trust='none'      -> pas encore de releve (shot jamais passe par l'outil)"""
    out = {"consumed": None, "latest": None, "stale": None, "trust": "none", "err": ""}
    if not record or not export_dir:
        out["err"] = "pas de releve (shot jamais cache par l'outil)"
        return out
    layers = record.get("layers") or {}
    consumed = layers.get(tracked)
    if consumed is None:  # tolere un match par sous-chaine (nommage variable)
        for k, v in layers.items():
            if tracked in k or k in tracked:
                consumed = v
                break
    latest = latest_product_version(export_dir, tracked)
    out["consumed"], out["latest"] = consumed, latest
    # le produit publie a-t-il bouge depuis notre cache ?
    prod = record.get("product")
    pv_rec = record.get("product_version")
    pv_now = latest_product_version(export_dir, prod) if prod else None
    if prod and pv_rec is not None and pv_now is not None and pv_now > pv_rec:
        out["trust"] = "uncertain"
        out["err"] = (
            "%s republie hors outil (v%03d > v%03d) : releve peut-etre perime"
            % (
                prod,
                pv_now,
                pv_rec,
            )
        )
    else:
        out["trust"] = "verified"
    if consumed is None:
        out["err"] = out["err"] or ("layer %s absent du releve" % tracked)
        return out
    if latest is None:
        out["err"] = out["err"] or ("aucun %s publie" % tracked)
        return out
    out["stale"] = latest > consumed
    return out


# --------------------------------------------------------------------------- #
#  Fraicheur : le snapshot est-il fiable, ou quelqu'un est passe par la scene ?
# --------------------------------------------------------------------------- #
def hip_version(hip_path):
    """N0 de version d'un .hip (SQ..._v027.hip -> 27), ou None."""
    m = _HIP_VER_RE.search(os.path.basename(hip_path or ""))
    return int(m.group(1)) if m else None


def latest_hip_version(hip_path):
    """Plus grande version .hip dans le dossier de `hip_path`, ou None."""
    d = os.path.dirname(hip_path or "")
    if not d or not os.path.isdir(d):
        return None
    best = None
    for f in glob.glob(os.path.join(d, "*.hip*")):
        v = hip_version(f)
        if v is not None and (best is None or v > best):
            best = v
    return best


def freshness(hip_path, snap_version, snap_mtime):
    """Confiance du snapshot vs l'etat disque :
    'obsolete'  : une version .hip PLUS RECENTE existe -> quelqu'un est passe.
    'uncertain' : meme version mais le .hip a ete re-sauve (mtime != snapshot).
    'verified'  : identique au dernier passage par l'app.
    'unknown'   : pas de metadonnees / hip introuvable."""
    if not hip_path or snap_version is None:
        return "unknown"
    latest_v = latest_hip_version(hip_path)
    if latest_v is not None and latest_v > snap_version:
        return "obsolete"
    snap_hip = hip_at_version(hip_path, snap_version)
    if snap_hip and snap_mtime:
        try:
            if abs(os.path.getmtime(snap_hip) - float(snap_mtime)) > 1.0:
                return "uncertain"
        except Exception:
            return "unknown"
    return "verified"


def hip_at_version(hip_path, version):
    """Le .hip de `version` dans le meme dossier (celui du snapshot), ou ''."""
    d = os.path.dirname(hip_path or "")
    if not d or not os.path.isdir(d):
        return ""
    for f in glob.glob(os.path.join(d, "*.hip*")):
        if hip_version(f) == version:
            return f
    return ""
