# nukeShotLoader

Outil Nuke d'Illogic : charge les assets Prism d'un shot (plates, rendus 3D/2D,
rotos, caméra), les tient à jour, et pilote les rendus précomp / compo sur Deadline.

Menu **Shot Loader** : Shot Asset Loader (`Ctrl+Alt+A`), Shot Render Manager
(`Ctrl+Alt+W`), Precomp ▸ Insert Precomp / Insert Compo Write / Refresh Precomps
(`Ctrl+Alt+R`) / Upgrade Precomps.

## Structure

```
menu.py            menu "Shot Loader" + watcher précomp (chargé via pluginAddPath)
src/
  core/            Python pur (ni nuke ni Qt) : config studio, découverte disque,
                   versions, statuts, prefs, fichiers JSON partagés
  scene/           graphe Nuke : nodes chargés, stamps, builder, rendus, render_order, submitter Deadline
  precomp/         système précomp v2 (voir precomp/__init__.py)
  ui/              dialog Qt : Loader, Render Manager, Logs (qt.py : PySide2/6)
  module_precomp.py, before_render_precomp.py, after_*.py
                   shims v1, seuls fichiers à la racine de src/ : les scripts v1
                   les exécutent par chemin absolu ou les importent par leur nom
toolsets/          templates v2 WritePrecomp.nk / WriteCompo.nk (menu ILGC Suite)
devtools/          lanceur de dev, environnement pipeline redirigé, déploiement
tests/             tests Python pur, Nuke réel, simulation Deadline, dialog
```

`src/` est ajouté au `sys.path` par le pipeline (pour les shims v1) : tout module posé à
sa racine devient importable par son nom par tous les outils. N'y ajouter rien d'autre.

## Précomps v2

Une précomp = une `PrecompWrite` (Write standard, `reading` off) suivie d'un switch
qui lit soit le live, soit un rendu précédent de cette Write (le cache).

- **Tout est décidé dans la GUI** (Refresh, soumission) et stocké en valeurs de knobs
  simples : switch `which` (0 = live, 1 = cache), chemin et plage du `CacheRead`.
  Aucun hook Python, aucune expression, aucune modification du graphe sur la farm :
  la farm rend exactement le script sauvegardé.
- Chaque dossier de version contient un `precomp.json` (hash du graphe amont,
  plage, script). Un cache n'est utilisé que si son hash est celui du graphe actuel
  **et** que toutes les frames nécessaires sont sur disque.
- Le hash est un hash de Merkle du contenu amont (valeurs de knobs, entrées, liens
  d'expressions, internes des groupes). Noms, positions, Dots et stamps n'y entrent pas.
  Les liens écrits `parent.Node.knob` / `root.Node.knob` sont suivis comme `Node.knob`
  (ex. une caméra d'overscan qui suit la caméra du shot).
- Après une modification en amont, le watcher repasse le switch en live (debounce 400 ms).
  Ces changements automatiques restent hors de l'historique d'undo.

**Rendu farm** (Render Manager) : pour chaque précomp à rendre, nouveau dossier de
version + manifest, switch routé sur la version en cours de rendu, `render_order`
distribués (précomps amont → précomps dépendantes → compo), Save Version, puis le
submitter Deadline (jobs séparés, ordre de rendu imposé → dépendances entre jobs).
Sans Deadline (Nuke vanilla), le Render Manager propose un rendu local.

**Bouton Render des Writes** (onglet Prism d'une PrecompWrite ou d'une Write compo,
`src/ui/write_render.py`, logique commune dans `ui/render_flow.py`). La case **Submit Job**
à côté décide, comme avec le bouton de Prism :

- **cochée** : la même soumission que le Render Manager, pour ce seul Write, sans ouvrir le
  dialog ni le submitter Prism. Précomps v1 impliquées : upgrade proposé. Précomps live en
  amont : proposées avec le Write (*Yes* : elles partent avec, render order en tête, le
  Write lit leurs rendus ; *No* : le Write seul, l'amont est rendu en live dans son job et
  rien n'est mis en cache ; *Cancel* : rien). Puis sanity check et submitter Deadline ;
- **décochée** : rendu local, comme avant — le rendu local de Prism, précédé pour une
  PrecompWrite de sa nouvelle version (`engine.render_here`). Sans Prism : `nuke.execute`
  pour une précomp, le Render de Nuke pour une Write compo.

**Render as previous version...** : toujours un rendu local dans une version existante,
jamais une soumission farm, quelle que soit la case Submit Job — pour réparer à la main des
frames cassées sur la farm.

Même dialog pour les deux (`ui/version_dialog.py`) : une version, les frames (manquantes
pré-remplies, à compléter par les frames cassées), *Render locally*.

- **Write compo** : refresh Prism d'abord (sortie du shot du script), puis les dossiers
  `v###` à côté de sa sortie (`render_ops.compo_versions`, frames de sa plage manquantes
  dans chacun ; pas de manifest, donc toutes proposées). Refusé si la sortie n'est pas dans
  le shot du script (script copié d'un autre shot, ou `FileNotInPipeline` de Prism).
  `render_ops.render_compo_into_version` : `fileName` pointé sur la version et le
  `beforeRender` de Prism coupé le temps du rendu (il viserait une nouvelle version),
  `nuke.execute` par plage, les deux remis. Ni sauvegarde de scène ni versioninfo réécrit ;
- **PrecompWrite** : versions de la précomp sur disque
  (`engine.rendered_versions`), seules celles rendues depuis l'état actuel du script (hash du
  manifest = hash courant) sont proposées : des frames rendues depuis un autre état ne
  correspondraient pas aux autres. Frames manquantes pré-remplies, à compléter par les
  frames cassées. `engine.render_into_version` : knob `versions` mis le temps du rendu sur la
  version choisie (refusé si le Write écrit ailleurs maintenant), `nuke.execute` par plage,
  knob remis, re-sync. Manifest inchangé, pas de nouvelle version.

**Onglet Prism des Writes** : identifier, Render, Render as previous version..., Submit Job,
puis un bloc en lecture seule :

- **version** (`render_version`, Int) : expression qui suit la sortie — `[value versions]`
  pour une précomp, le dossier de version du `fileName` de Prism pour une Write compo
  (`.../v038/...` → 38, 0 sans dossier de version, jamais d'expression en erreur pour le
  sanity check). Utilisable ailleurs (`[value WriteCompo.render_version]`). Verrouillée en
  READ_ONLY (lisible, non éditable) ; Nuke ne sauve pas ce flag : un `knobChanged` des Writes
  le repose à l'ouverture du panneau (`commands.lock_version_display`, menu.py), et l'upgrade
  au chargement remet l'expression si elle a été écrasée. Ignorée par le hash ;
- **filepath** (`render_output`, PyCustom_Knob, `ui/knob_widgets.py`) : la sortie telle
  qu'elle s'évalue (`renderpath` d'une précomp, `fileName` de Prism), sélectionnable,
  relue toutes les 500 ms tant que le panneau l'affiche (Prism la réécrit seul). Un
  Text_Knob n'évalue pas le TCL, d'où le widget ;
- **Open In Explorer** : le dossier de la sortie ; tant que cette version n'est pas rendue
  (Prism affiche la suivante), la dernière version sur disque ; sans aucune, le dossier
  existant le plus proche.

Cachés (valeurs gardées) : comment, location, filepath + Refresh, previous filepath, Open
In / Create Read, media conversion, publish to Shotgrid, et le `versions` +/- des précomps
(`spec.HIDDEN_TAB_KNOBS`), plus un séparateur qui se retrouverait collé à un autre. Le bloc
est ajouté à la fin de l'onglet (Nuke n'ajoute des knobs qu'en fin de node) : sauté si
l'onglet Prism n'est pas le dernier du Write.

Tout est porté par les nodes eux-mêmes : les templates (`toolsets/`) l'ont, et les Writes
des scripts existants sont upgradés à l'ouverture du script en GUI
(`commands.upgrade_prism_tabs` → `nodes.upgrade_prism_tab`) : scripts des boutons remplacés
quand ce sont ceux de Prism (`pcore.appPlugin.startRender` / `renderAsVersion`) ou l'ancien
bouton v2 (`engine.render_locally`), Render as previous version... et Submit Job rendus
visibles (valeur de la case gardée), knobs inutilisés cachés. Hors undo, et un script non
modifié le reste : l'upgrade est enregistré à la prochaine sauvegarde. Un script
personnalisé, les autres Writes et les PrecompWrites v1 (upgradées par *Upgrade Precomps*)
ne sont pas touchés. Ni les boutons ni les flags n'entrent dans le hash : les caches restent
valides. *Upgrade Precomps* fait aussi cet upgrade (Writes créées depuis le menu Prism après
l'ouverture).

Une précomp ne passe « Submitted vNNN » que si des jobs sont réellement partis. Le
submitter ne renvoie rien (et écrit ses réglages même sur Cancel) : son exécution est
observée (`src/scene/deadline.py` — réponse de son dialog, questions posées ensuite,
`JobID` renvoyé par Deadline pour chaque job). Dialog annulé, question refusée ou jobs
refusés par Deadline : la préparation est défaite (`engine.discard_renders` — manifest et
dossier de version supprimés, knob `version` remis), la précomp retrouve son état d'avant
(Live, Live (forced)…) et la prochaine soumission reprend le même numéro. Un dossier qui
contient déjà des frames n'est jamais touché. Le `.nk` sauvegardé pour la soumission, lui,
reste (une version de script non soumise).

Soumission partielle : le résultat est suivi Write par Write (`deadline.LAST_JOBS` : Write,
job pris par Deadline ou sa réponse). Une Write attendue sans job — refusée par Deadline,
ou jamais envoyée par le submitter (exception, Write plus sélectionnée : le submitter du
studio n'envoie que les Writes sélectionnées, vérifiées juste avant chaque job) — donne
`render_ops.PARTIAL` : ses précomps sont remises comme avant (pas de faux « Submitted »), la
compo n'est marquée soumise que si son job est parti, et l'artiste reçoit un avertissement
avec la liste et la raison (détail par job dans le Script Editor). Les Writes à envoyer sont
resélectionnées après chaque job, et le refresh automatique comme la resynchro des précomps
sont suspendus pendant toute la soumission (SQ0180-SH0660, 8/10 : *Render Compo and
Precomps* n'avait envoyé que le job MATTE, sans rien dire).

Vignette Prism : à chaque Save Version, Prism rend l'entrée du viewer pour la vignette de
la scène. Une soumission sauvegarde avec les switches routés vers des rendus qui
n'existent pas encore : ce rendu échouait sur leur `CacheRead` (« Flipbook render
failed »). La vignette est donc rendue avant le routage (`render_ops.scene_thumbnail`) et
fournie à Prism pour cette sauvegarde.

**Sanity check** (`src/sanity/`) : juste avant le submitter, chaque rendu lancé depuis le
Render Manager passe une série de règles, dans un dialog avec barre de progression. Une
règle sans problème passe à la suivante ; sinon la liste des nodes fautifs s'affiche avec
*Fix* (corrige, re-vérifie, continue) et *Close* (rien n'est soumis). Seuls les nodes dont
dépend le rendu sont vérifiés (entrées, liens d'expressions, intérieur des groupes). Si un
fix a modifié le script, l'action de rendu repart du script corrigé : les règles sont
revérifiées sans dialog, qui ne revient que si l'une d'elles échoue encore.

| règle | détecte | fix |
|-------|---------|-----|
| Fichiers hors réseau | nodes qui lisent un fichier (Read, DeepRead, caméra, géo…) hors de `I:/`, `R:/`, `B:/` (`Config.NETWORK_ROOTS`) | copie dans `<shot>/Renders/fromLocal/<node>/` puis repath |
| Majuscules dans les Expression | identifiants en majuscules dans les Expression / DeepExpression (`B`, `A`… lus de travers par Nuke sur la première frame de chaque tâche farm) | passage en minuscules ; références de nodes et de knobs, variables temporaires, fonctions et TCL intacts |
| Expressions de knob en erreur | expression que Nuke ne peut pas évaluer (node ou knob renommé / supprimé, `parent.` inexistant, faute de syntaxe, TCL en erreur) : elle vaut 0 sans rien dire, dans le viewer comme sur la farm | expression retirée (*No animation*) : le knob garde ce 0 |
| Bounding box | bbox en entrée d'une Write rendue dépassant le format de plus de 20 % (`Config.BBOX_TOLERANCE`) | Crop au format inséré avant la Write |

Expressions en erreur : Nuke n'expose pas l'état d'erreur, l'expression est donc
réévaluée par TCL dans le contexte du node. Trois garde-fous évitent de signaler (et de
supprimer) une expression valide : un nom qui existe n'est jamais une erreur (`translate`
dans le champ x d'un Transform désigne `translate.x`), le knob doit valoir 0 sur les
frames sondées, et le node doit être adressable par son nom (un node interne homonyme
d'un knob de son groupe ne l'est pas). Les TCL des knobs texte (chemins de fichier) ne
sont pas vérifiés. Retirer une expression change le hash des précomps en aval.

Lire ce qu'une expression vise peut demander à Nuke de valider tout un amont sur un arbre
froid (un knob de gizmo : 16 s mesurées sur SQ0010-SH0010 v050). Un premier contrôle
remplace donc par 1 ce qui ne peut pas porter de référence cassée — `width`, `height`,
`bbox.*`, `format.*`, et les références `Node[.Enfant].knob[.champ]` / `parent.knob` /
`root.knob` dont le node et le knob existent (`settled_expression`) — et seule une
expression qui échoue encore est évaluée telle quelle : 27 s → 0,8 s sur v050, mêmes
erreurs trouvées. Les frames sondées excluent la frame courante hors de la plage du script.

Coût de la règle bounding box : une Write précédée d'un Crop (ou d'un Reformat « to
format » sans *preserve bounding box*), éventuellement derrière des Dots, est jugée sur
les knobs de ce node, sans calcul. Les autres sont mesurées par Nuke (`node.bbox()`), qui
valide tout l'arbre amont : instantané quand Nuke l'a déjà validé (cas normal en session :
~10 ms pour 9 Writes sur un script de 15 000 nodes), plusieurs secondes s'il doit d'abord
ouvrir les fichiers sources (script à peine ouvert, sources qui viennent de changer). Le
dialog affiche alors la Write en cours, *Close* interrompt entre deux Writes, et toute
mesure de plus d'une seconde est écrite dans les logs avec sa durée.

Ajouter une règle : une sous-classe de `sanity.rules.Rule` (`check(context, progress)`,
`fix`) ajoutée à `RULES`.

**Caméras** (`src/scene/cameras.py`) : une Camera3 rend depuis ses knobs — des courbes
sauvegardées dans le script : c'est ce que le viewer et la farm utilisent. Avec *read from
file*, Nuke y recopie la caméra du fichier, mais seulement si le panneau de propriétés du
node existe : sur une caméra jamais ouverte dans la session, `reload` incrémente son
compteur sans toucher aux knobs, et la caméra reste figée sur son ancienne version alors que
son knob `file` (et le Loader) indiquent la nouvelle.

Load et Update ne passent donc plus par cet import : le Shot Loader lit l'USD lui-même
(`pxr`, fourni avec Nuke) et écrit dans les knobs les mêmes courbes que l'import de Nuke
(`rot_order` XYZ, une clé par frame de la plage du stage : translate, rotate, scaling,
focal, apertures, near / far, focus, f-stop). *read from file* est décoché — Nuke ne
relira jamais le fichier par-dessus — et `file` garde le chemin (version affichée, détection
par le Loader). Avant de rendre la main, la transformation que Nuke calcule depuis ces
knobs est comparée à celle du fichier sur chaque frame ; au moindre écart le node est
remis dans son état d'avant. Les rotations sont gardées continues d'une frame à l'autre
(pas de saut de 360° entre deux clés, qui ferait tourner la caméra sur les sous-frames du
motion blur) : au passage du gimbal les angles peuvent donc s'écrire autrement que ceux de
l'import Nuke, pour la même orientation.

Ce que le bake ne reproduit pas est refusé, node intact, et confié à l'import de Nuke
(panneau ouvert le temps du chargement, sans popup) : formats autres qu'USD, stage Z-up,
transformation avec shear ou miroir, lens shift, caméra orthographique, plusieurs caméras
sans sélection. Une caméra déjà figée dans un script existant n'est pas détectée (le
Loader la voit à jour) : la repasser par un Update, ou ouvrir ses propriétés et presser
*Reload*.

**Versions** : un rendu va toujours dans la version qui suit le plus haut dossier
`v###` existant, quelle que soit la valeur du knob `version` de la Write : pas de trou
dans la numérotation (une version incrémentée à la main mais jamais rendue est celle
qui sera rendue).

**Version de la Write compo** : même règle, obligatoire — au submit et au rendu local
(Render Manager, ou bouton Render décoché via Prism) elle pointe sur la version qui suit
sa dernière vraie version : rendue, ou soumise à la farm (`render_ops.refresh_compo_write`).

- Prism marque une Write « en cours de rendu » quand un rendu d'elle démarre et ne retire
  la marque que par son `afterRender` ; tant qu'elle est marquée, son refresh renvoie le
  chemin de ce rendu sans toucher `fileName` (SQ0050-SH0210, 7/10 : deux submits dans v028).
  La marque est effacée avant le refresh ; les Write compo reçoivent l'`afterRender` de Prism.
- Prism greffe ses knobs (et son `beforeRender`) sur toute Write créée, identifier = la tâche
  de la scène : la Write temporaire de chaque flipbook — dont la miniature de chaque *Save
  Version* — crée en rendant un dossier `Compo/vNNN` vide (seulement `versioninfo.json`),
  qui faisait sauter un numéro (SQ0180-SH0610 : v036 vide, rendu en v037). Ces dossiers
  inutilisés au-dessus de la dernière vraie version sont supprimés avant chaque rendu
  (`release_unused_versions` : rien d'autre que `versioninfo.json` dedans) ; notre propre
  miniature est prise avec `PRISM_NUKE_WRITE_ADD_KNOBS=0` (interrupteur de Prism) ; une
  version soumise reçoit `shotloader_submitted.json` (en usage avant sa première frame).
- Le chemin est vérifié sur le disque (déplacé sinon, nommage Prism gardé), le refresh fait
  avant la miniature, et revérifié après la sauvegarde de version.

**Précomps hors flux** (qui n'alimentent pas la Write compo) : exclues des rendus
habituels. Un node désactivé ne laisse passer que son entrée 0 (B d'une Merge) : une
précomp qui n'arrive que par l'entrée A d'une Merge désactivée est hors flux. Quand il y en a, deux boutons apparaissent sous le tableau :
*Render All Out of Stream* (celles en live) et *Render Selected Out of Stream* (même en
cache). Elles partent sans le compo. Leur render order est calculé depuis leur propre
amont : juste après la dernière Write qu'elles lisent (précomps du flux comprises, avec
l'ordre que leur donne le compo). Un identifiant partagé avec une autre précomp est
refusé (même dossier de rendu).

Clic droit sur les lignes : ouvrir le dossier ou le cache, rendus adaptés aux lignes
sélectionnées (dans le flux ou hors flux), Force Live / Cancel Force Live.

Boutons de ligne et sélection multiple : un bouton de ligne pressé sur une ligne
sélectionnée agit sur toute la sélection — Freeze et Hide / Recover dans le Loader, Force
Live dans le Render Manager. La ligne cliquée donne le sens (geler ou dégeler, forcer ou
annuler) et les autres suivent. Sur une ligne hors sélection, ou seule sélectionnée, le
bouton n'agit que sur elle.

**Force Live** (colonne à droite du status de chaque précomp dans le Render Manager) : passe
à la version suivante et ignore les rendus existants, même si le graphe n'a pas changé
(source réécrite au même chemin, gizmo mis à jour…). Inactif sur une précomp déjà live
(rien à ignorer). Status « Live (forced) », bouton
enfoncé (gris foncé). Les précomps en aval repassent aussi en live, puisque leur cache
contient l'ancien rendu. Tant que cette version n'est ni rendue ni soumise, un nouveau
clic annule la décision : version précédente et caches reviennent. Une fois rendue, le
bouton se relâche ; le presser à nouveau force la version suivante. La marque
(`precomp_live_from`, knob caché de la Write) entre dans le hash ; `precomp_force_undo`
garde l'état d'avant pour l'annulation.

**Scripts v1** : ils continuent de rendre (en live, sans cache) grâce aux shims.
Pour passer en v2 : Render Manager ▸ *Upgrade Precomps* (ou menu Precomp). Lancer un
rendu qui implique des précomps v1 (la Write rendue ou son amont) propose l'upgrade :
Non, rien n'est rendu ; Oui, conversion du script puis rendu.

## Développement

`devtools\launch_nuke15_dev.bat [pipeline|vanilla] [script.nk]`

- `pipeline` (défaut) : exactement ce que lance le launcher Prism du projet
  (`devtools/launch_nuke.py`) — environnement machine, variables d'environnement du
  projet (`pipeline.json`) et de son entrée « Nuke 15.1 » (`00_Pipeline/Configs/launcher.json` :
  OCIO, licence…), init studio (Prism, Deadline, Stamps, gizmos ILGC) — avec ce checkout
  chargé à la place du shot loader du pipeline (`devtools/pipeline_env`, en dernier dans
  `NUKE_PATH`, redirige ses `pluginAddPath` et les templates ILGC). Le projet est celui du
  script passé en argument, sinon le projet courant de Prism. Ces réglages sont lus à
  chaque lancement, jamais recopiés : le .bat suit le pipeline.
  `python.exe -s devtools\launch_nuke.py [script.nk] --dry-run` affiche l'environnement
  sans lancer Nuke.
- `vanilla` : Nuke nu + Shot Loader seul (pas de Prism ni de Deadline).

## Tests

```
"C:\Program Files\Nuke15.1v5\python.exe" -s tests\run_tests.py [static] [core] [release] [sanity] [camera] [engine] [farm] [ui] [--keep] [--update-golden]
```

| suite    | contenu | durée |
|----------|---------|-------|
| `static` | tous les modules compilent | < 1 s |
| `release` | `release.py` sur une copie sandbox du pipeline (vrai v1 + templates) : simulation sans effet, deploy, re-deploy sans changement, rollback depuis le share à l'identique (fichiers + templates), retour en avant, historique | ~4 s |
| `camera` | caméras USD (générées par le test) bakées dans les knobs d'une Camera3 sur Nuke réel : valeurs du fichier, transformation recalculée par Nuke, rotations au-delà de 180° et au gimbal, plages de frames, fichiers refusés (node intact), repli sur l'import Nuke | ~2 s |
| `sanity` | règles du sanity check sur Nuke réel : détection, copie + repath, minuscules, expressions en erreur (et expressions valides non signalées), Crop, bbox lue sur les knobs == bbox mesurée par Nuke | ~2 s |
| `core`   | Python pur : fichier de prefs partagé (jamais réécrit s'il est illisible), écritures JSON atomiques avec nouvelles tentatives, manifests et numéros de version, couverture de frames | ~3 s |
| `engine` | moteur précomp sur Nuke réel : upgrade v1, stabilité du hash entre sessions, soumission annulée / refusée / envoyée (faux submitter Deadline), rendu, cache == live, invalidation sélective, templates | ~1 min 40 |
| `farm`   | simulation Deadline dans l'environnement pipeline : un process Nuke par job, scène copiée comme le path mapping, `-t` + `nuke.execute` en stdin (batch mode) et `-x`, jobs enchaînés par render_order, logs scannés avec les motifs d'erreur du plugin Deadline ; preuves par falsification que les jobs dépendants lisent les caches ; scripts v1 rendus après déploiement | ~2 min 30 |
| `ui`     | dialog Qt piloté avec un faux module `nuke` : vérifications explicites puis comparaison à `tests/qt/expected.json` (`--update-golden` le régénère : relire le diff) | ~2 s |

Les rendus de test vont dans un sandbox temporaire (`--keep` le conserve), jamais sur
un share de production. Rien n'est soumis à la vraie farm.

## Déploiement

`devtools\release.py` (Python de Nuke : `"C:\Program Files\Nuke15.1v5\python.exe" -s`).
Chaque commande est une simulation tant que `--apply` n'est pas passé.

```
release.py status                      release en place et historique
release.py list                        releases archivées (* = en place)
release.py deploy [--apply]            ce checkout -> pipeline
release.py rollback [<id>] [--apply]   release précédente (ou <id>) -> pipeline
```

Une release = le dossier `R:\pipeline\pipe\nuke\script\nukeShotLoader` + les templates
ILGC `R:\pipeline\pipe\nuke\gizmos\WritePrecomp.nk` / `WriteCompo.nk`. Toutes celles qui
ont été en place sont archivées dans `R:\pipeline\pipe\nuke\_releases\nukeShotLoader\<id>\`
(hors des plugin paths de Nuke), avec `history.json`.

- `deploy` vérifie que le checkout compile, archive ce qui est en place (au premier
  déploiement : le shot loader v1), archive le checkout (sans `devtools/`, `tests/` ni
  caches) et l'installe. Le dossier garde son chemin (les scripts v1 exécutent leurs hooks
  par chemin absolu). Chaque fichier est remplacé via une copie temporaire (un Nuke qui
  démarre pendant ce temps ne lit jamais un fichier à moitié écrit), `menu.py` en dernier.
- `rollback` réinstalle la release précédente, ou n'importe quelle release archivée
  (y compris pour revenir en avant). Il se lance aussi depuis le share, sans ce checkout :
  `python.exe -s R:\pipeline\pipe\nuke\_releases\nukeShotLoader\release.py rollback --apply`.
- Retour au v1 : les scripts upgradés en v2 entre-temps s'ouvrent et se rendent toujours
  (la farm n'a besoin d'aucun code), mais le v1 ne resynchronise plus leurs switches : un
  switch resté sur son cache y reste après une modif amont. Le rollback affiche la ligne à
  exécuter dans ces scripts pour les repasser en live.

À faire hors session des graphistes : un Nuke déjà ouvert garde l'ancienne version en
mémoire jusqu'à son redémarrage (idem pour un rollback).

## Robustesse

- Le fichier de prefs du projet (hidden, freeze, packages de tous les shots) et les
  `precomp.json` sont partagés entre sessions : écriture atomique (fichier temporaire
  puis remplacement), nouvelles tentatives si une autre session le lit à cet instant,
  et un fichier illisible n'est jamais réécrit.
- Le dialog suit le script ouvert : si un autre shot est ouvert dans le même Nuke, il se
  reconstruit ; en attendant (auto-refresh en pause), Load / Update / rendus sont refusés.
- Auto-refresh toutes les 15 s (`Config.AUTO_REFRESH_MS`), suspendu pendant un rendu,
  submitter Deadline ouvert, ou fenêtre minimisée (la synchro des précomps fige Nuke
  ~0,3 s sur une compo lourde) ; refresh immédiat quand elle réapparaît.
- Une version choisie dans le menu déroulant du Loader (rollback ou update) garde son
  statut à travers les refresh automatiques et les rescans, tant que le dialog est ouvert
  et qu'elle n'a pas été appliquée par un Update.
- Le chargement d'une caméra ne pose aucune question (bake par le Shot Loader ; pour les
  fichiers confiés à l'import de Nuke : `suppress_dialog`). En filet de sécurité, un popup
  de Nuke qui apparaîtrait quand même est fermé automatiquement et son texte écrit dans
  l'onglet Logs. Seuls les popups de Nuke (`QMessageBox` titré « Nuke ») sont fermés
  ainsi, jamais un autre dialog (sanity check, questions du Shot Loader, submitter Deadline).
- Load, Update, Duplicate, Upgrade et Force Live font chacun une seule étape d'undo ; les
  changements automatiques (statuts, routage, render_order) restent hors de l'undo.
- Le refresh automatique ne reconstruit le Render Manager que si quelque chose a changé,
  et jamais pendant la saisie d'un nom ou d'un identifiant.

## Points d'attention

- *Submit Scene* doit rester activé dans le submitter Deadline (défaut studio) : le job
  embarque une copie du `.nk`, donc un Ctrl+S après soumission ne change pas ce que la
  farm rend.
- Chaque soumission d'une précomp invalide crée une nouvelle version. Les anciens
  dossiers peuvent être purgés, sauf ceux qu'un script utilise encore comme cache :
  son `CacheRead` échouerait (volontairement) plutôt que de rendre du noir. Un
  Refresh dans la GUI repasse alors la précomp en live.
