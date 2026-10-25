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
- **headless_guard** `src/lop_update_cache/headless_guard.py` — pur Qt : aucune fenêtre
  modale ne peut geler hython (sanity check studio…), cf « Parité avec un submit GUI ».
  Le moteur Maya garde sa propre copie (`recache_maya.install_headless_dialog_guard`).
- Lancé depuis Houdini par un **shelf tool** (`houdini_shelf_tool.py`) qui passe le projet
  courant (`pcore.prismIni`) + la scène via env `LOP_UPDATE_CACHE_PROJECT` / `_HIP`.
  Bouton **From scene** = remet dans le champ la scène `_HIP` (celle ouverte dans Houdini
  **au lancement** ; le champ, lui, reprend la dernière scène mémorisée). Pas de shelf Maya.
- **Choix de la scène** : panneau de gauche **toujours ouvert** (`SceneBrowser`), qui a
  remplacé le dialogue `Choose scene...` (`ProjectPicker`, supprimé). Cf section dédiée.
- **Moteur Maya** `src/lop_update_cache/recache_maya.py` — tourne DANS **mayapy**. Une
  scène `.ma` dans le champ bascule la fenêtre en **mode RIGS** (cf section Maya).
  `maya_refs.py` = lecture texte du `.ma` (références + states Prism), 0 Maya.

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
Le node maison `illogic::usd_layer_stack` (parms `sequence`/`shot`/`resolved`,
multiparm `version#` en **lecture seule**) se re-résout **au dernier publish** à chaque
load (`OnLoaded` → `rescan()` → `update()`), **sauf les lignes épinglées** (2.1+, cf
« Pins » plus bas). Lui demander « quelle version pointes-tu ? » après un load répond
donc « la dernière » : la question n'a plus de sens.
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
- **Deux versions du node coexistent** : `::1.0` (`illogic_usd_layer_stack.hda`) et
  `::2.0` (`lop_illogic.usd_layer_stack.2.0.hda`, 12/08/2026). `is_layer_stack` teste la
  **sous-chaîne** `illogic::usd_layer_stack`, sans le suffixe de version → les deux
  passent, et les suivantes aussi. Ne PAS resserrer ce test sur une version.
  La 2.0 ajoute `checkall`/`checknone` et, par sublayer, `enable#` et `parts#`.
  Une **2.1** existe deja en prod (frederic_2603) : mêmes parms, rien à changer.
  Vérifié en session live sur un node 2.0 : `resolved` **suit `enable#`** (décocher
  `cam` retire son chemin) et un département décoché a son `version#` **vide** → notre
  lecture principale (`resolved`) *et* le repli multiparm sont justes tous les deux, il
  n'y a rien à filtrer. `parts#` est resté vide dans toutes les configs testées.

### Pins du usd_layer_stack (2.1+) — état « pinned »
Depuis la 2.1, une ligne peut être **épinglée** (`pin#` = `vNNN` au lieu de `latest`).
Vérifié dans le PythonModule de la **2.2 de prod** : `OnLoaded` et le bouton `reload`
appellent `rescan()` → `update()`, qui **garde** la version épinglée. Avant le correctif
(16/10, A/B sur le moteur déployé) : anm épinglé v017, latest v019 → **OUTDATED pour
toujours**, l'update re-cachait en v017, et le log disait « reload » sans rien dire du pin.
- `layer_stack_pins(node)` → `{dept: pin}` des lignes **actives** figées (une ligne
  décochée ne charge rien : son pin ne compte pas ; HDA sans `pin#` → `{}`). Deux
  sources : le pin de ligne (`vNNN`) et, en **2.5+** (pas encore publiée au 16/10), le
  parm `shotversion` = `vNNN` qui fige toutes les lignes sans pin propre sur les
  versions du container `Export/USD/vNNN` → `shot vNNN` (pin de ligne prioritaire,
  comme dans le HDA). Testé sur la 2.5 de `dist/` : shot v132 → anm v018, latest v019.
- `preview.mark_pins(layers, pins)` (pur, partagé moteur / preview / UI) : le pin porte sur
  la **ligne** = tout le département (`_layer_anm_*` : le master ET les éléments qu'il
  référence). Layer épinglé en retard → `pinned_behind=True`, `stale=False`.
  `combine_layers` remonte `pinned` → état **`pinned`** (ni OUTDATED ni coché par défaut).
  En OU, un AUTRE layer suivi périmé rend quand même le shot OUTDATED.
- Statut : `pins` + `pinned_layers` par item. Le **preview** (disque seul, ne voit pas le
  node) réapplique les `pins` du snapshot → un Reload rapide ne perd pas l'état.
- Sans relevé : `no_record` comme avant, mais le latest disque des layers épinglés est lu
  pour l'afficher (« v017 (pinned, latest v019) »).
- **L'outil ne dépingle JAMAIS** (choix de l'artiste) : un update forcé garde le pin, le dit
  dans le log (« pins … GARDES ») et dans la confirmation (« PINNED layers kept »).

### Plusieurs layers suivis (OU / ET)
UI : le cas courant (UN layer) est un simple **dropdown** ; le multi-layer vit derriere
une **roue crantee** ("advanced sorting" : cases a cocher + ANY/ALL). Un menu a cases
avait ete tente a la place du dropdown -> illisible (cf ci-dessous).
- Le dropdown liste les layers que la scene consomme VRAIMENT. Quand plusieurs layers
  sont suivis il montre en tete une entree de synthese (`Anm / Cam`) : il ne peut pas
  n'en afficher qu'un et mentir. Y choisir un layer fait retomber sur un seul.
- Zero layer suivi est refuse a l'application (plus rien ne serait jugeable), meme si le
  dialogue permet de tout decocher avant de valider.
- ⚠️ **Ne JAMAIS remplir ce dropdown depuis `usd.departmentOrder` (pipeline.json)** :
  41 entrees sur yuka_2604, 40 sur frederic_2603 -- DEUX generations de nommage cote a
  cote (`lgt`/`Lighting`, `cmp`/`Compositing`, `anm`/`Animation`...) plus des collisions
  de casse (`fx`/`FX`, `cfx`/`CFX`), alors qu'une stack de shot compte 2 a 8 layers.
  C'etait le repli quand aucune scene n'est chargee -> dropdown illisible. Sans scene,
  on n'affiche que le layer memorise.
Le suivi n'est plus mono-layer : on coche N layers et un mode.
- **OU** : périmé dès qu'**un** des layers suivis a bougé. **ET** : seulement quand ils ont
  **tous** bougé.
- Un layer suivi que le shot **ne consomme pas** est **ignoré** (dans les DEUX modes) :
  son absence n'est pas une information. Il ressort dans `ignored` → tooltip de la
  cellule + note grise à côté du bouton. Si **aucun** layer suivi n'est consommé →
  `n/a`, jamais « up to date ».
- Logique à **3 états** : `None` = indécidable (version non résolue, relevé manquant).
  En OU un vrai périmé tranche ; sinon `None` se propage. Un `None` ne devient JAMAIS
  « à jour » -- c'est la règle qui a déjà coûté deux faux verts (cf binaire, relevés).
- **UNE seule implémentation** : `preview.combine_layers`, appelée par l'UI (`_combined`)
  ET par le moteur (`apply_tracked`). L'UI ne peut pas afficher un verdict et le moteur
  en appliquer un autre. L'UI passe un `--tracked-layer` PAR layer + `--tracked-mode`.
- UI : le combo est devenu **un bouton à menu de cases** (`KeepOpenMenu`, qui ne se
  referme pas à chaque clic) — même encombrement qu'avant. Le séparateur de l'entête DIT
  le mode : `Anm / Cam` (OU), `Anm & Cam` (ET). Colonne : `k/n stale` dès 2 layers.
- Sidecar : `tracked_layers` + `tracked_mode`, et `tracked_layer` (1er) reste **écrit** —
  une version plus ancienne de l'outil ouvrant le même json partagé retombe sur ses pieds.

### Scenes rangees sous /Assets (≠ entites asset)
Une scene peut vivre sous `03_Production/Assets/<catégorie>/<asset>/Scenefiles/...` tout
en cachant de **vrais shots** (vérifié sur `frederic_2603`, `Assets/FX/snowSetup` : 77
imports, **tous** en `mode='shot'`). Ne pas confondre l'**emplacement de la scène** avec
l'**entité cachée**.
- Le moteur n'avait donc **rien** à changer : entités = shots, tout le reste suit.
  Vérifié en `--status` sur cette scène (1 item, `SQ0020/SH0050`, ancré render, apparié
  par topologie).
- Le seul blocage était le **picker** (aujourd'hui le panneau de gauche), qui ne
  parcourait que `Shots/` → bascule **Shots / Assets** (même arbre, libellés
  `Category`/`Asset`), et il se place du bon côté quand la scène courante est un asset.
  Les gabarits Prism `@...@` sont masqués.
- `_find_shots_up` reconnaît les deux racines : sans ça, un projet ne se déduit pas d'une
  scène rangée sous Assets.
- `layer_stack_shot` en `mode='asset'` renvoie le **nom d'asset nu**, comme le repli
  `ent.get('asset')` de `shot_from_cache_output` → les deux sources s'accordent.

### Plusieurs filecache par shot + produit REEL
- Un shot peut avoir **plusieurs `lop_filecache`**, publiant des produits **différents**
  (vérifié : `frederic_2603` → `_layer_fx_snow_still` v008 **et** `_layer_fx_snow_sim`
  v009, aucun bypassé). En scène de rendu on n'en attachait qu'**un** (`[0]`) : l'autre
  n'était jamais re-caché. L'item porte maintenant `caches` (tous) ; `cache` reste le 1er
  pour compat. Échec sur l'un → pas de version-up (livrable incomplet).
- ⚠️ **Le produit publié ne se déduit PAS du parm `department`.** Les deux caches
  ci-dessus disent tous les deux `department='fx'` → `_layer_fx_master`, un produit
  qu'aucun des deux ne publie. Le relévé pointait donc un produit **inexistant** et le
  garde-fou « republié hors outil » était silencieusement neutralisé.
  → `cache_output()` lit le **chemin de sortie résolu** (`usdExport … getOutputName()`),
  le département ne sert plus que de repli.
  (⚠️ `getOutputEntity()` renvoie l'entité **source** — sur ce cache : produit
  `_layer_cam_master`, département Animation. Ce n'est PAS la sortie.)
- Relévé : `products` = {produit: version} de **tous** les caches ; `product`/
  `product_version` (le 1er) restent écrits pour les versions antérieures de l'outil.
  `preview.published_outside` teste **tous** les produits.
- **Choix des caches par l'artiste** (même modele que les renders et la chaine SOP) :
  colonne `Caches` cliquable -> `CachePickerDialog`. Les caches sont présentés par leur
  **produit** (`_layer_fx_snow_sim`), pas par leur nom de node (`lop_filecache3`), qui ne
  dit rien. Persistance : `cache_unselected` dans le sidecar (on stocke les **décochés**,
  donc un cache ajouté plus tard au setup est coché par défaut). "Apply to all shots"
  propage **par produit** (les chemins de node changent d'un shot à l'autre).
- ⚠️ **`--cache-plan` : entrée ABSENTE = tous, liste VIDE = aucun.** Les deux doivent
  rester distincts : sans ça, tout décocher recacherait tout. Tout décocher est
  légitime : on bumpe l'import et on soumet le render sans re-cacher.
- **Repli par shot** : on préfère les imports réellement **en amont d'un export**
  (`cfg["exported_imports"]`). Sur la scène FX, **1 import sur 77** l'est — les 76 autres
  sont des stacks caméra. Sans ce départage, suivre `cam` appariait le cache à une
  **caméra** (reproduit en test). Préférence, pas filtre dur : si aucun candidat n'est
  câblé on garde tout, plutôt que de perdre l'appariement.

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

### ⚠️ "sim inatteignable" : illisible ≠ rien à re-simuler
Le moteur refuse de republier un shot FX dont la sim ne peut pas être relancée (sinon il
publierait l'ANCIENNE sim avec la NOUVELLE anim, et le shot passerait au vert). Mais il
déduisait "inatteignable" de l'**absence de filecache SOP**, ce qui confond deux cas :
- réseau **illisible** (aucun node visible) → on ne peut rien affirmer, on s'abstient ;
- réseau **lisible sans aucun cache** (setup procédural, layer *still*) → il n'y a
  simplement rien à re-simuler : **il faut recacher normalement**.
Seul `fx_opaque()` (aucun `allSubChildren()`) bloque désormais.
- ⚠️ `isLockedHDA` **ne discrimine pas** : les DEUX sopcreate de `frederic_2603` le sont,
  l'un expose 3 nodes et 0 cache, l'autre 380 nodes et 3 filecaches SOP.
- La chaine SOP se calcule sur **tous** les caches de l'item, pas seulement le premier :
  sinon un item est déclaré bloqué à cause d'un cache qui n'a rien à simuler, alors qu'un
  autre cache du même shot expose une vraie chaine.
- ⚠️ **Cet outil n'est pas un outil FX** : ce garde-fou débordait sur tout ce qui a un
  `sopcreate` en amont, cfx et lighting compris.

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

### Réglages ferme (frames, prio, chunk, pool…) — bouton **Farm ▸**
Demandé par Thomas (16/10). Deadline reçoit ce que portent les **widgets du state** Prism
au moment du publish (`Prism_Deadline_Functions.sm_render_submitJob`) : la fenêtre de
submit GUI ne fait que les montrer. L'outil pose donc les MÊMES widgets avant le submit.
- Réglables : frames (`Custom` début-fin, ou `Expression` avec tokens `{first} {middle}
  {last}` résolus sur la plage de **chaque** shot → `{first}-{last}x10` a un sens pour
  toute la scène), `sp_rjPrio`, `sp_rjFramesPerTask`, `sp_rjTimeout`,
  `sp_dlConcurrentTasks`, `sp_machineLimit`, `cb_dlPool`/`cb_sndPool`/`cb_dlGroup`,
  `chb_rjSuspended`, job haute prio (`gb_prioJob`, `sp_highPrio`, `e_highPrioFrames`).
- **Override, pas remplacement** : clé absente = valeur de la scène (chaque node a la
  sienne : prio 65 / 60 sur beaverDam). `--farm-plan` json `{"*": {...}}`, appliqué à
  chaque render soumis ; **en mémoire seulement** dans l'UI (oublié au changement de
  scène), jamais dans le sidecar : la prio se décide au moment d'envoyer.
- Valeur impossible (pool/group absent de Deadline, prio hors bornes, expression
  illisible) → `FarmSettingError` → le render n'est **pas** soumis (jamais d'envoi avec
  d'autres réglages que ceux demandés). farm-plan illisible → aucun render soumis.
- `--status` émet `renders[].farm` (valeurs actuelles + listes pools/groups) : le
  dialogue affiche « scene: … » à côté de chaque champ. Coût non mesurable (state déjà
  construit à l'ouverture de la scène).
- ⚠️ Le job **husk** de rendu prend son groupe dans l'env projet
  (`PRISM_HUSK_DEADLINE_GROUP=husk_grp` dans pipeline.json frederic, vu sur un job GUI) :
  le Group choisi s'applique aux autres jobs (cleanup…). Dit dans le dialogue.
- **Vérifié par dry-run** (vrai submitter Prism, sortie en dossier temporaire, envoi à
  Deadline intercepté au niveau `CallDeadlineCommand` → callbacks `preSubmit_Deadline`
  studio exécutés, aucun job) : prio 88/95, frames 1001-1020 avec split du job haute prio
  (1001,1020 / 1002..1019), chunk 2, machine limit 4, pool, Suspended → tels quels dans
  les jobs. Limite : le callback USD compilé `sm_render_getDeadlineParams` (conversion
  husk) était débranché pendant ce test (code opaque, risque d'écriture en prod) → job
  de type Houdini, comme les jobs GUI yuka. Test de bout en bout réel : à faire dans un
  bac à sable.

### Parité avec un submit GUI (audit du 16/10)
Le bouton Submit (`Farm_Submitter.submit`, source Prism lisible) = `sm.publish` avec les
parms du node. Tout ce qui tourne dans un submit GUI passe par `sm.publish` → **mêmes
callbacks/hooks** en headless. Vérifié dans le hython de l'outil : plugins studio chargés
(`husk_extra_settings` : script husk du studio monkeypatché + tuiles/autocrop ;
`variable_deadline` : OPTI / limites de textures Karma ; `ranch_exporter` : pre/post-job
ranch si `ILL_RANCHCOPY_ENABLED` ; `auto_cleaner` ; `clear_comment`), env projet appliquée
au `changeProject` (`ILL_RANCHCOPY_ENABLED=1`, `PRISM_HUSK_DEADLINE_GROUP`, OCIO…). Écarts
trouvés et corrigés :
- `sanityChecks` était **forcé à False** → maintenant celui du **node** (comme la GUI).
  Sans interface, les checks Prism intégrés ne font que logguer (`runSantityChecks`
  renvoie True) : pas de blocage possible.
- Le check studio `TileFramePerTask` ne regarde que `hou.selectedNodes()` → en headless
  il ne vérifiait **rien**. Le node est maintenant **sélectionné** avant le publish.
- Hook projet `preRender` : sa branche GUI pose `ILLOGIC_TEMP_NODE` puis… sort si
  `not hou.isUIAvailable()`. Rejoué par `prerender_gui_effects` avec **sa** fonction
  `catchInfo` (même module que Prism). Lu seulement par `Hooks/old/preSubmit_Deadline.py`
  (désactivé) : parité de principe.
- 🔴 **Sanity check studio en headless = gel** : le hook `prePublish` lance
  `sanity_check.main` à CHAQUE publish (cache ou render) ; un check en échec →
  `MainDialog.exec()` → hython bloqué à vie. `headless_guard.install()` (module partagé,
  pur Qt) répond comme la GUI : **ERROR → refus** (« Publish anyways » grisé), warnings
  seuls → on publie, tout est loggué. **Reproduit en vrai** : tuiles + 2 frames/task →
  `Tile Frame Per Task` ERROR → refusé, nommé, sans gel. Un refus annule le publish SANS
  erreur sur le node : `submit_render` et `process_item` le détectent
  (`headless_guard.refused_since`) → KO explicite (avant : un cache non écrit = « OK »).
- `sm.publish` renvoie `None` si un hook prePublish annule, `False` si erreurs → KO.
- `PRISM_LAUNCH_ENV` (env du profil launcher Prism, copiée dans les jobs : OCIO,
  limites Karma…) n'existe que si l'outil vient du **shelf Houdini** (le shelf passe
  `os.environ`). Lancé ailleurs → avertissement dans la confirmation et le log.
- Restent **volontairement** différents : `saveScene`/`incrementScene` (l'outil gère la
  sauvegarde lui-même, avant le submit), le commentaire (celui de l'outil, pas le parm
  `comment` du node), `useVersion` (« next » ; le module LOP render n'a pas
  `getWriteVersionFromNode`, tous les nodes vus sont en `autoVersion`).

## Maya : mise à jour des rigs + exports (mode RIGS)
Séquence validée avec Thomas : **update → vérifier → incrémenter → exporter**.
- **Panneau de scènes** : liste `.hip*` ET `.ma` (le `.mb`, binaire, n'est jamais proposé :
  illisible sans Maya). `scene_kind()` (extension) décide du mode : Houdini = vue historique
  inchangée ; Maya = colonnes `Rig | Version | State | References`, layers suivis et
  `Load Scene` masqués, bouton **Exports n/m ▸** à côté du switch de sauvegarde.
- **Lecture sans Maya, instantanée** : les `file -r` ET `fileInfo "PrismStates"` (json
  échappé MEL) sont en tête du `.ma`. `maya_refs.rig_status` = une ligne par **asset**
  (un rig est référencé N fois) ; `maya_refs.scene_exports` = states `USD Export` /
  `Export` (Playblast exclu : pas de viewport en batch). Produit publié
  (`export_product`) vérifié contre `state.ui.getProductname()` dans Maya : Layer +
  sublayer → `_layer_<dep>_<sublayer>` ; Custom → `product` ; Export → `productname`.
- **Défaut des exports** = states cochés dans le State Manager de la scène (comme les
  renders). Choix explicite stocké dans le sidecar : `export_states` = uuids cochés
  (`None` = défaut ; un state ajouté après un choix explicite reste décoché).
- **Moteur** `--apply --rigs <ids> [--export <uuids>] [--no-save] --comment` :
  1. bootstrap Prism dans mayapy (QApplication AVANT `maya.standalone`, poser
     `PrismInit.pcore`), ouverture avec toutes les références ;
  2. swap `cmds.file(new, loadReference=rn)` + **veto** : failed edits après > avant →
     `refused_lost_anim`, ni save ni export ;
  3. version-up Prism (ou rien en `--no-save`, commentaire des exports suffixé
     `(scene not saved)`) ;
  4. exports **un par un**, `sm.publish(executeState=True, states=[item],
     sanityChecks=True, saveScene=False, successPopup=False)` = clic droit > Execute
     (un state rangé dans un Folder ne lance que lui : `Folder.executeState` filtre
     sur `execStates`). En `noUI`, sanity checks et popups Prism sont **logués**.
     Réussite = **nouvelle version sur disque** (pas le retour de `publish()`, faux dès
     qu'un hook logue une erreur).
- `--rigs` **absent** = tous les périmés (CLI) ; `--rigs` **sans valeur** = aucun (l'UI
  l'envoie pour « exports seuls » — sinon le moteur prenait tous les rigs).
- **Verdict** : bloc `>>>MAYA_RESULT>>>{json}<<<` en fin de run (`ok`, `dry_run`,
  `refused_lost_anim`, `save_failed`, `export_failed`…). L'UI lit le verdict, pas le code
  de sortie ; **pas de bloc = Maya mort en route** → « non traité », jamais un succès.
- Hooks studio : mayapy lit `Maya.env` (`MAYA_ENV_DIR`) → PYTHONPATH studio présent,
  `usd_chaser` (postExport des `_layer_anm_*`) tourne comme en GUI. `sanity_check` et
  `rig_split_variants` ne sont PAS importables en batch → `prePublish` les saute.
- Env de mayapy (`Main._maya_env`) : on retire PYTHONPATH/PATH de Houdini et du venv (l'UI
  est lancée depuis le shelf Houdini, même python 3.11 des deux côtés), `PYTHONHOME`,
  `QT_PLUGIN_PATH` ; `PYTHONIOENCODING=utf-8`, `PYTHONUNBUFFERED=1`.

## Panneau de scènes (gauche, toujours ouvert)
Demandé par Thomas (idée reprise du batch publisher de Quentin : l'arbre des shots
toujours visible) → plus besoin d'ouvrir `Choose scene...`.
- **3 colonnes côte à côte** (demande de Thomas, pas de département « en bas ») :
  `Sequence / Shot` | `Department` | `Task`. Au-dessus : `Shots`/`Assets`, filtre sur
  `séquence/shot` (`SH0125`, `SQ0020/SH01` ; Entrée = ouvre le seul résultat), ⟳ = relire
  le disque.
  - Col. 1 : arbre des entités (`Shots` : séquence > shot, `_sequence` compris ;
    `Assets` : catégorie > asset). Aucun asset imbriqué sur yuka/frederic (vérifié).
  - Col. 2 : les départements du shot **qui ont au moins une scène** (un shot vide affiche
    `no .hip / .ma scene`, non cliquable). Changer de département ne charge rien.
  - Col. 3 : **une ligne par tâche = sa dernière version** ; déplier pour les anciennes,
    affichées `vNNN` (nom complet si le fichier n'est pas de la même famille). Les tâches
    **sans scène** sont masquées (Prism en crée à la pelle : 14 sur 17 pour yuka
    SQ0020/SH0125).
  - Département montré à l'ouverture d'un shot : celui de la scène chargée, sinon le
    dernier choisi, sinon le seul.
- **Tailles par défaut** : fenêtre = 1560×900 + 20 % = **1872×1080, bornée à 95 % de
  l'écran** (sinon elle passe sous la barre des tâches d'un écran 1080p) ; panneau
  **580 px** (colonnes 210 | 150 | 200), borné 420..1100.
- **Tout est relu sur le disque à la volée**, sans cache : mesuré 0,05 s pour les 29
  séquences / 180 shots de frederic_2603, 0,08 s pour les 73 scènes d'un shot yuka.
- Un clic sur une tâche/version **charge la scène** (= le champ Scene, puis
  `_on_hip_changed` comme avant). Le **couple département/tâche est retenu** : cliquer un
  autre shot charge directement la même tâche s'il l'a → revue d'une séquence en un clic
  par shot. S'il ne l'a pas : rien n'est chargé (le département retenu reste affiché).
- Sens inverse : `_sync_browser` (appelé par `_on_hip_changed`) montre la scène du champ
  (Browse, From scene, version-up) **sans rien recharger**. Une version absente de la liste
  (version-up tout juste écrite) force une relecture du dossier.
- Le panneau est **désactivé pendant un run** (`_busy`) : changer de scène en plein run
  mélangerait sidecar / scène sauvée.
- ⚠️ Clic sur une séquence = déplie/replie. Qt n'émet pas toujours le même nombre de
  `itemClicked` sur un double-clic → `expandsOnDoubleClick` coupé + 2e clic dans
  l'intervalle de double-clic ignoré (`_toggle_group`). Vérifié avec la vraie séquence
  Windows (press, release, DblClick, release) : **`QTest.mouseDClick` n'envoie QUE le
  DblClick**, il ne reproduit pas un vrai double-clic.
- QSettings (par utilisateur) : `browser_width` (largeur du panneau), `shots_root` (dernier
  projet vu, dernier recours de `_shots_root`).

## Presets de scène (partagés par projet)
Demandé par Thomas : enregistrer une scène sous un nom (« cfx brush ») que **tout le
monde** sur le projet charge en un clic, sans savoir où elle est rangée.
- Bouton **★ Presets (n)** à côté du champ Scene : un clic sur un preset met sa scène dans
  le champ (puis `_on_hip_changed` comme d'habitude, le panneau suit). Dans le même menu :
  `Save current scene as preset...` et `Delete preset ▸` (confirmation).
- Stockage : `<projet>/00_Pipeline/Configs/lop_update_cache_presets.json`, à côté des
  configs projet de Prism (`launcher.json`, `omits.json`). Les artistes écrivent déjà dans
  `00_Pipeline` (leurs `ErrorLog_*.txt`). ⚠️ **Pas** `00_Pipeline/PresetScenes` : ce sont
  les gabarits de scène de Prism, il les proposerait à la création d'une scène.
- Un preset stocke la **famille** de la scène (dossier de tâche relatif au projet +
  `scene_family` = nom sans version ni extension), pas un fichier → il suit les
  version-ups et ouvre toujours la **dernière** version. Scène disparue (renommée,
  déplacée) → message clair, champ inchangé.
- Menu **relu à chaque ouverture** (un preset d'un collègue apparaît sans relancer). Le
  compteur du bouton n'est relu qu'au changement de projet : `_on_hip_changed` tourne à
  chaque frappe. Écriture : relecture juste avant + fichier temporaire + `os.replace`
  → deux enregistrements simultanés ne s'écrasent pas.
- Nom unique (casse ignorée) : même nom = confirmation, le preset garde sa place.
- ⚠️ Sous-menu `Delete preset` créé **une fois** et ré-attaché à chaque ouverture : un
  `addMenu(titre)` par ouverture empile des QMenu (`clear()` ne les détruit pas) et
  PySide 6.11 finit par renvoyer un wrapper « already deleted » (reproduit).
- `scene_family` reprend **à l'identique** l'ancienne logique de `_scene_key` (clé des
  sidecars).

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
  `tracked_layer`, `scene_version`/`scene_mtime`, `export_states` (scène Maya : uuids des
  exports cochés). Le "Reset local settings" (QSettings par-user : hython, mayapy,
  projet) N'efface PAS ce json. Même règle pour un `.ma` : `<scene>.lopcache.json` à côté.
- Projet : dropdown dans la fenêtre principale (`(auto-detect)` = env Houdini / dérivé du
  .hip ; sinon projets sous `I:/` avec `00_Pipeline/pipeline.json`).
- **Partagé, par projet** : les presets de scène,
  `<projet>/00_Pipeline/Configs/lop_update_cache_presets.json` (cf section Presets).

## ⚠️ Landmines
- 🔴 **Un save Maya headless RÉÉCRIT les USD publiés** si on ne fait rien. mayapy ne lit
  pas `userPrefs.mel` → mayaUSD à son défaut usine `mayaUsd_SerializedUsdEditsLocation
  = 1` (« save all edits back to usd files »). Constaté : le version-up de test du 12/09
  a ré-écrit `SBX/testSplit/Export/USD/v005/*.usda` (même contenu, CRLF → LF). Les
  artistes sont à **2** (edits sérialisés dans le `.ma`) : `SH0125/Export/USD/v016` n'a
  jamais été touché par des dizaines de saves GUI. Fix : `keep_published_usd_untouched`
  pose 2 après l'ouverture, avant tout save (2 et pas 3 : 3 perdrait les edits USD d'un
  artiste stockés dans le `.ma`).
- 🔴 **Aucune fenêtre modale ne doit exister en batch** : le hook `prePublish` lance le
  `sanity_check` studio (`I:/<projet>/.pipelines_deploy/general/scripts`, importable une
  fois Prism chargé) qui fait `MainDialog.exec()` dès qu'un check échoue → mayapy **gelé**
  (vu : 10 min, CPU 0). `install_headless_dialog_guard` remplace `exec()` : check en
  ERROR → refus (en GUI « Publish anyways » est grisé), WARNINGs seuls → publié (la GUI le
  permet), toute autre modale → refusée ; tout est logué et remonté (`exports[].sanity`).
- **`SizeCommentaire` lit `sm.e_comment`** (le champ), pas l'argument `comment=` de
  `publish()` → vide en batch = échec garanti. Le moteur remplit le champ.
- **Plugin studio `pre_playblast_plugin`** (viewports/HUD/burn-in) : son `prePublish`
  plante en batch (`cmds.getPanel` → None) et Prism **annule tout publish**. Seul lui est
  neutralisé (`mute_ui_only_callbacks`) ; tout autre callback qui plante annule toujours.
- **Export raté = version cassée sur disque** : Prism crée `vNNN/` avant que mayaUSD
  n'écrive (vu : `_layer_cam_camera/v004`, `.usdc` vide de 492 o, sur une scène où deux
  camRigs donnent le même prim path). Le moteur le signale (`broken_version`), l'UI dit
  de la supprimer — sinon elle passe pour la dernière.
- **`cmds.file(open=True)` lève sur des erreurs de lecture** (rig dont la version a été
  supprimée du disque) alors que la scène est ouverte, comme les warnings GUI → on
  continue si `sceneName` est bien la scène. `rig_status` marque `missing`.
- **Un export `.ma/.mb` avec « import references » recharge la scène depuis le disque**
  en fin de publish (`sm.reloadScenefile`). Scène sauvée : on recharge la nouvelle version,
  OK. Scène **non** sauvée : les swaps (en mémoire) sont perdus → le moteur **s'arrête**
  plutôt que de lancer les exports suivants avec les anciens rigs.
- **Quel Houdini ? celui dont le python a une integration Prism.** Prism 2.0.18 fournit
  `python3.7/3.9/3.10/3.11libs`. Houdini 21.0.729 = python **3.11** (OK) ;
  Houdini 22.0.368 = python **3.13** (KO : PrismInit ne se charge pas). `detect_hython`
  ne retient donc que les installs dont le python embarque a une integration ; sinon un
  poste qui desinstalle sa version de reference bascule en silence sur la plus recente
  et plante. La version du python se lit sur `<HFS>/bin/python3XX.dll` -- ⚠️ le DOSSIER
  `python3XX` de l'install MENT (22.0.368 contient python310/311/313 et tourne en 3.13).
- ⚠️ **Tri des `python<X.Y>libs` : NUMERIQUE.** En lexical `python3.9libs` >
  `python3.11libs` -> on chargeait l'integration **3.9** (PySide2) et l'erreur affichee
  etait `ModuleNotFoundError: No module named 'PySide2'`, qui ne dit rien de la vraie
  cause. Meme piege que le tri des versions Houdini.
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
- Tests = smoke offscreen (`QT_QPA_PLATFORM=offscreen`) ; probes réelles en hython contre
  `yuka_2604`.
- ⚠️ **Les tests UI doivent tourner avec le python de l'UI (`.venv/Scripts/python.exe`),
  PAS hython.** L'UI tourne en **PySide6 6.11** (uv), hython embarque **6.5**. La 6.5
  tolère un nom d'enum court sur une instance (`box.AcceptRole`), la 6.11 lève
  `AttributeError` → crash en prod dans `_guard_newer_scene`, alors que tous les tests
  passaient sous hython. Toujours écrire l'enum scopé : `QMessageBox.ButtonRole.AcceptRole`.
- ⚠️ **Ne pas mesurer de pixels de texte en `offscreen` sous 6.11** : sans vraie police il
  prend un repli ~2× plus large (612 px vs **305 px** en plateforme `windows`, identique
  à la 6.5). Un test de largeur y échoue à tort ; les mesures réelles se font en `windows`.
- ⚠️ Les tests qui construisent `Main()` doivent **isoler les QSettings** (fichier ini
  temporaire) : sinon ils lisent/écrivent `HKCU\Software\Illogic\lop_update_cache`, les
  vrais réglages de l'utilisateur.
- Console Windows : un `print()` de `▸` plante en cp1252 → `PYTHONIOENCODING=utf-8`.
