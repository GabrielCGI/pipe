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
  Bouton **From scene** = remet dans le champ la scène `_HIP` (celle ouverte dans Houdini
  **au lancement** ; le champ, lui, reprend la dernière scène mémorisée). Pas de shelf Maya.
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
- Le seul blocage était le **picker**, qui ne parcourait que `Shots/` → bascule
  **Shots / Assets** (mêmes colonnes, libellés `Category`/`Asset`), et il s'ouvre du bon
  côté quand la scène courante est un asset. Les gabarits Prism `@...@` sont masqués.
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

## Maya : mise à jour des rigs + exports (mode RIGS)
Séquence validée avec Thomas : **update → vérifier → incrémenter → exporter**.
- **Picker** : liste `.hip*` ET `.ma` (le `.mb`, binaire, n'est jamais proposé : illisible
  sans Maya). `scene_kind()` (extension) décide du mode : Houdini = vue historique
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
