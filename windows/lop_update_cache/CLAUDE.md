# CLAUDE.md — lop_update_cache

Outil pipeline Illogic (projet Prism `yuka_2604`, `I:/yuka_2604`). Re-cache **headless**
les layers cfx/fx quand l'anim (ou un autre layer tracké) d'un shot est mis à jour, **sans
ouvrir la GUI Houdini**. Auteur direction : Thomas (TD FX). Claude code.

## Architecture (2 morceaux)
- **UI** `src/lop_update_cache/cfx_recache_ui.py` (PySide6) — lancée par `main_ui.bat`
  (`uv run`). Ne charge PAS Houdini : elle pilote le moteur en **sous-process hython**
  (QProcess) et parse son stdout (marqueurs `>>>STATUS_JSON>>>…<<<`, `>>>PROGRESS>>>`,
  `>>>SUBPROGRESS>>>`, `>>>SAVED_SCENE>>>`).
- **Moteur** `src/lop_update_cache/recache_cfx.py` — tourne DANS hython. `--status`
  (JSON read-only), `--apply` (bump import + re-cache), `--discover`. Bootstrap Prism via
  `PrismInit.prismInit()` (headless : `changeProject(pipeline.json)` obligatoire).
- **preview** `src/lop_update_cache/preview.py` — pur Python (0 Houdini) : détection de
  péremption par lecture disque (voir plus bas).
- Lancé depuis Houdini par un **shelf tool** (`houdini_shelf_tool.py`) qui passe le projet
  courant (`pcore.prismIni`) + la scène via env `LOP_UPDATE_CACHE_PROJECT` / `_HIP`.

## Faits pipeline (vérifiés)
- Prism 2.0.18 (`C:\ILLOGIC_APP\Prism\2.0.18`). Produit Prism = `.../<SHOT>/Export/
  <produit>/vNNN/<fichier>`. Container shot = produit `USD` → `.../Export/USD/vNNN/
  <...>.usda`, ses `subLayers` pointent des versions de layer master
  `.../_layer_<x>_master/vNNN/...`.
- ⚠️ **La règle « un container est toujours .usda » est violée en prod.** Mesuré :
  `MASTER/MT0020/Export/USD/v008/*.usdc` est un vrai crate binaire (magic `PXR-USDC`) ;
  1045 `.usdc` sous les produits Export ; **144 produits / 441 ont un latest binaire** ;
  `SQ0010/SH0050/Export/_layer_set_main` alterne usda/usdc quasi à chaque version.
  → **Ne jamais déduire le format de l'extension ni de la règle** : tester le contenu
  (`preview.is_ascii_usd`, magic `#usda`). `pxr.Sdf` lit les deux, le preview texte non.
- Nodes : import `prism::LOP_Import::1.0` (parm `filepath`), cache USD
  `prism::lop_filecache::1.0`, caches SOP `filecache::2.0` + `prism::Filecache::1.0`.
- **Péremption = token du LAYER tracké** (défaut `_layer_anm_master`), PAS le n° du
  container (le cfx re-bumpe le container → faux positifs). Comparaison : version du
  layer dans le container consommé vs dans le dernier container.
- Une scène contient **N shots** (cfx MASTER = 20 shots ; fx = multi-shots aussi).

### Détection AGNOSTIQUE au layer importé (vérifié sur yuka_2604)
La scène peut importer le **container du shot** OU **directement un layer master**
(`.../_layer_anm_master/v012/...`). `stack_layers` (moteur) / `path_layers` (preview)
renvoient donc **`subLayers` ∪ {produit désigné par le chemin : sa version}**, le
produit propre primant (c'est la version réellement consommée). Le layer tracké est
alors trouvé dans les deux cas, sans rien savoir du container.
- ⚠️ **Un `_layer_<x>_master` n'est PAS une feuille** : il sublayer ses
  `_layer_<x>_class` / `_layer_<x>_main`. Un fallback « pas de subLayers → c'est le
  produit » ne se déclencherait donc **jamais** → fusionner, pas deviner.
- ⚠️ Les `subLayers` réels sont soit **relatifs forward-slash**, soit **absolus Windows
  backslash** (`@I:\...\v001\x.usdc@`) → **normaliser `\` → `/` avant de regexer**, des
  deux côtés, sinon le preview rate des layers que le moteur voit (bug corrigé).
- Prism résout `getLatestVersionFromPath` / `getPreferredFileFromVersion` /
  `getCachePathData` aussi bien sur le produit `USD` que sur `_layer_anm_master` → le
  bump et l'appariement par shot marchent sur les deux formes.
- Layer tracké **non consommé** par l'import → `no_layer` → l'UI affiche
  **`n/a (not consumed)` en gris**, surtout PAS « up to date » : la scène ne lit pas ce
  layer, il ne peut donc pas la périmer.
- Le preview parse **uniquement le bloc `subLayers = [...]`**, pas tout le head : sinon
  il ramasserait les `references`/`payloads` versionnés que `pxr.Sdf` ignore → moteur
  et preview divergeraient.
- **Parité moteur/preview = invariant, mais SUR L'ASCII SEULEMENT** : `stack_layers`
  (pxr.Sdf) et `path_layers` (regex texte) renvoient la même chose sur un `.usda`
  (mesuré : 2301/2301 fichiers réels). Sur un **crate binaire** le preview perd les
  subLayers alors que Sdf les voit → d'où la règle ci-dessous.
- 🔒 **Le preview ne conclut QUE s'il a tout lu.** `refresh_entry` sort en
  `preview=False` (garde le snapshot moteur, sans y toucher) si le container consommé
  **ou** le dernier est binaire. Sinon `parse_container_layers` renvoie `{}`, le layer
  tracké prend `latest=None` → `stale=False` → **faux « up to date »**, et un
  `outdated` correct du moteur se fait **repeindre en vert** par le scan de fond.
  Un `{}` de « je n'ai pas su lire » ne doit JAMAIS se lire « rien n'a bougé ».
  (Régression réelle introduite puis corrigée : `latest_product` acceptant `*.usdc`.)
- `latest_product` prend la version sur le **nom du dossier** (fiable même si le
  fichier est binaire) et ne saute PAS une version binaire pour retomber sur une ASCII
  plus vieille — ce serait mentir sur la dernière version publiée.

### Péremption par RELEVÉ DE CACHE (source de vérité, agnostique au type de node)
Le node maison `illogic::usd_layer_stack::1.0` (parms `sequence`/`shot`/`resolved`,
multiparm `version#` en **lecture seule**) se re-résout **toujours au dernier publish**
(`OnLoaded` → `update()`). Lui demander « quelle version pointes-tu ? » après un load
répond donc toujours « la dernière » : la question n'a plus de sens.
→ **Au moment du cache** on relève ce qui a réellement été consommé, et on compare ce
relevé au disque (`preview.record_state`). Marche pour les **deux** générations de node.
- Relevé (sidecar, clé `cached[<shot>]`) : `{layers: {produit: version}, product,
  product_version, export, at}`. `product`/`product_version` = ce que le cache a publié →
  si le disque est passé devant, quelqu'un a re-caché **hors outil** : `trust=uncertain`,
  on le **dit** au lieu de mentir. Pas de relevé → `no_record`, jamais « up to date ».
- ⚠️ **`cfg["cache_records"]` est chargé UNE FOIS au démarrage du process.** Le
  rafraîchissement de fin de run (le `STATUS_JSON` ré-émis après l'apply) rejuge donc les
  shots avec le relevé d'**avant** le cache → le shot qu'on vient d'exporter ressort
  PÉRIMÉ et la ligne reste rouge jusqu'à un Reload. `harvest_records` réinjecte les
  relevés frais dans `cfg` avant ce refresh. (Bug signalé en prod, corrigé.)
- ⚠️ Le `usd_layer_stack` est **invisible du collecteur de dépendances Prism** (4 deps
  relevées au lieu de 18) → ne pas s'appuyer sur les deps Prism pour la péremption.

## Appariement cache→import (robuste nom + câblage)
- Shot du cache = `usdExport.getStateFromNode(cache).ui.getOutputEntity()` (sortie, pas nom).
- Import = celui qui **importe le même shot** (`import_for_shot`, départage par présence du
  layer tracké) ; topologie `inputs()` en dernier recours. FX : la topo ne relie pas le
  cache à l'import (caches SOP figés) → appariement par shot obligatoire.

## FX : chaîne de re-sim SOP
- Un `lop_filecache` FX relit des bgeo SOP FIGÉS → le republier seul ne re-simule pas.
  `fx_sop_chain()` remonte au `sopcreate`, liste les filecaches SOP disque (ordre par
  dépendance). UI : colonne "SOP caches" cochable ; `--fx-plan` = sélection par shot.
  Apply : bump import → re-sim caches SOP cochés (pressButton `execute`) → lop_filecache.
- HDA sim **locked** = caches internes inatteignables → chaîne vide ("- (locked?)").
  Un shot FX **périmé + locked** est **SKIP** (pas de bump import, pas de republish : sinon
  l'import passerait "à jour" et masquerait la péremption) → flag `LOCK`, re-sim manuel
  requis. Un shot FX non-locked mais tout décoché republie quand même (choix artiste).
- **`--force`** (l'UI le passe toujours) = cache TOUS les shots cochés, même à jour :
  cocher = intention explicite. (Le locked-skip prime quand même sur `--force`.)

## Lighting : submit farm des `prism::LOP_Render`
Une scène **lighting** a, par shot, un `shot_SHxxxx_LightingCache` (cache, géré comme les
autres) **ET** un `Render_shot_0x0` (`prism::LOP_Render` → `usdrender_rop` / husk / Karma
XPU → **Deadline**). L'outil peut, après le bump import + re-cache du LightingCache,
**re-soumettre le render à la ferme** — l'action exacte de l'artiste.
- **Découverte / appariement** : `collect_renders()` trouve les `prism::LOP_Render` (le
  type EXACT du node de tête, pas les `usdrender_rop` internes). Shot lu depuis le parm
  **`customContext`** (JSON Prism `{sequence, shot}`), fallback parm `context`
  (« Shot - SQ0010-SH0050 ») — **pas** d'API render incertaine. `renders_for_shot()`
  attache les renders à l'item du **cache** du même shot.
- ⚠️ **`executePressed`/`pressButton(execute)` NE SOUMET PAS en headless** (mesuré : un
  apply réel logue « 1 OK » sans créer de job). Le bouton `execute` avec `submitJob` ouvre
  le dialogue **`Farm_Submitter`** (UI) qui ne s'`.show()` pas headless → rien ne part.
- ✅ **Voie headless = répliquer `Farm_Submitter.submit()`** (source Prism,
  `Prism_Houdini_Node_Filecache.py`) SANS dialogue :
  ```
  state = pcore.getPlugin("USD").api.lopRender.getStateFromNode({"node": node})
  state.ui.gb_submit.setChecked(True)          # <- gb_submit = le switch FARM (False = local)
  sm = pcore.getStateManager() or pcore.getStateManager(create=True)
  sm.publish(executeState=True, states=[state], saveScene=False, ...)
  ```
  C'est **`gb_submit`** (pas le bouton) qui décide farm-vs-local. `lopRender` est
  **Cython-compilé** (`.pyd`) → pas de source lisible ; on s'appuie sur `Farm_Submitter`
  qui est en clair et partagé.
- 🔒 **Sécurité** : `submit_render()` coche `gb_submit` **explicitement** et **REFUSE**
  (lève, aucun `publish`) si pas d'API `lopRender`, pas de `gb_submit`, **pas de submitter
  farm** (`cb_manager` vide) ou pas de `StateManager` → jamais de render local par mégarde.
  Préfère le manager **Deadline** dans `cb_manager`.
- ✅ **PROUVÉ EN LIVE (2026-07-20)** : `sm.publish → True`, job Deadline créé en headless
  (hython 596, uiAvailable=False) sur SH0070. La recette marche.
- **UX : cocher un shot lighting = re-cache PUIS render** (pas d'opt-in séparé — cacher
  des lights seul ne sert à rien). L'outil détecte le lighting via la présence de
  `renders`. Le re-cache du LightingCache reste le prérequis (intègre le nouvel anim).
- **Layers (executions) cochables** : un `LOP_Render` a un multiparm **`executions`**,
  chacune rendant UN layer (context option `layer` = CHARS/BG/FG/MG/VOLUME) avec un toggle
  **`execution_enabled_#`**. `read_render_executions()` les lit ; la colonne "Renders"
  (`RenderPickerDialog`) les liste **cochables**, défaut = ceux **Enabled sur le node**
  (behavior 1). Tout décoché = re-cache seul, pas de render.
- **`set_render_executions()`** écrit le `execution_enabled_#` selon les layers cochés,
  dans `apply_render_selections()` **AVANT le save** → l'état part dans le version-up
  (behavior 2). Puis `submit_renders()` (APRÈS le save) presse le submit. Le submit envoie
  tous les layers **restés Enabled** = 1 job Deadline par node.
- **Ordre** : `apply_render_selections` (set Enabled) → **save version-up** →
  `submit_renders` (submit). On **ne soumet PAS** le render d'un shot dont le re-cache a
  échoué (`rep.ok is False`) ni un render sans layer coché.
- **Persistance** : `--render-plan` json `{cache_id: [{node, layers}]}`. Sidecar :
  `render_layers[shot] = [layers cochés]` (override ; défaut = Enabled node). "Apply to
  all shots" propage **par nom de layer** (communs aux shots).

## Preview sans Houdini (le gros gain de temps)
- Le sidecar json (voir Persistance) stocke le dernier `status` vérifié + `import_path` par
  shot + `scene_version`/`scene_mtime`. À l'ouverture d'une scène : **affichage instantané**
  du snapshot, puis **scan disque en QThread** (`preview.refresh_status` : glob des `vNNN`,
  parse texte du dernier container `.usda`) → maj des gaps de version. Houdini seulement au
  re-cache (Load Scene = vérité terrain).
- **Fraîcheur** (`preview.freshness`) : version .hip plus récente sur disque → `obsolete` ;
  même version mais mtime ≠ snapshot → `uncertain` ; sinon `verified`. Badge dans l'UI.
- 🔒 **Garde-fou avant un apply** (`_guard_newer_scene`) : le moteur charge **le .hip du
  champ** (`--hip`), pas « la dernière version ». Si une version **plus récente** existe,
  il chargerait l'**ancienne** puis version-uperait par-dessus → le travail fait entre les
  deux **disparaît** de la nouvelle version. L'UI prévient et propose **[Use latest] /
  [Continue anyway] / [Cancel]**. (En `uncertain` — même version re-sauvée — pas de
  problème : le moteur relit le fichier à jour depuis le disque.)

## Persistance
- **Partagé, par scène** : `<scene_sans_version>.lopcache.json` **à côté du hip sur I:/** →
  tout artiste qui ouvre a les mêmes params. Contient : `status` (snapshot), `fx_unselected`
  (sélections SOP par shot, on stocke les **décochés**), `render_layers` (layers à rendre
  par shot lighting ; override, défaut = Enabled node), `cached` (relevés de cache, cf
  ci-dessus — le moteur les **émet**, l'UI est le **seul écrivain** du json),
  `tracked_layer`, `scene_version`/`scene_mtime`. Le "Reset local settings" (QSettings par-user : hython,
  projet) N'efface PAS ce json.
- Projet : dropdown dans la fenêtre principale (`(auto-detect)` = env Houdini / dérivé du
  .hip ; sinon projets sous `I:/` avec `00_Pipeline/pipeline.json`).

## ⚠️ Landmines
- **SEGFAULT multi-versions Houdini** : tous les postes ont plusieurs Houdini. Lancer le
  hython 596 avec un env 729 → `import hou` charge le mauvais `_hou.pyd` → crash à l'import.
  Fix : `Main._houdini_env` épingle HFS+bin du hython choisi et purge les autres install
  (filtre par **numéro de build**, gère la forme courte 8.3 `HOUDIN~1.729`). N'agit que via
  l'UI → **toujours lancer par l'UI/shelf, jamais `hython` à la main**. Assertion HFS dans
  le moteur = erreur claire au lieu d'un segfault muet.
- **PySide6** : ne pas injecter le site-packages uv (6.11) dans le PYTHONPATH de hython
  (Houdini a le sien 6.5 → collision Qt).
- **FX "No frame range is set on the source stage"** : le `lop_filecache` FX doit être en
  `trange` "Output Shot Context" (comme cfx), pas "From Stage" (cassé headless). Fix = côté
  setup/HDA. Le moteur DÉTECTE l'échec (`node_errors` récursif : erreur sur le ROP interne)
  → pas de version-up sur échec.
- **`LOP_muteDepartments/update` cook errors** : pré-existants (plantent sur un load
  headless), non fatals, pas causés par l'outil. Bruit console.

## Conventions
- **Version gérée par la CI studio** (auto-bump de `version="x.y.z"` dans `pyproject.toml`).
  On la LIT (`importlib.metadata` / pyproject), jamais on ne la fixe. Affichée dans le titre.
- **Repo = fork GitLab** `thomas_courtois/lop_update_cache` de `illogic/standalone/
  lop_update_cache`. Workflow = **MR** vers le canonique. Hook pre-commit **ruff-format**
  reformate au 1er commit → re-`git add` + re-commit. Package uv/hatchling, py 3.11.
- Tests = smoke offscreen (`QT_QPA_PLATFORM=offscreen`) via hython ; probes réelles en
  hython contre `yuka_2604`.
