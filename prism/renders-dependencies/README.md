# Renders Dependency Checker - Interface de visualisation des dépendances USD

## Prérequis
- Python 3.11.9
- QtPy

## Installation de l'environnement Python

1. Clonez le projet ou récupérez les sources.
2. Créez un nouvel environnement virtuel :
   ```
   python -m venv .venv
   ```
3. Activez l'environnement virtuel :
   - Windows : `.\.venv\Scripts\activate`
   - Mac/Linux : `source .venv/bin/activate`
4. Installez toutes les dépendances du projet :
   ```
   pip install -r requirements.txt
   ```

## Fichiers principaux
**r_core.py** :
  - Contient la logique de scan des layers USD et la génération des statuts de chaque layer (up-to-date, outdated, missing, etc.).
  - Cas particulier pour le layer **_layer_lgt_master** (lighting) :
    - Si la version la plus récente du layer lighting est plus récente que le render, le programme vérifie la version précédente (n-1).
    - Si la date du fichier de la version n-1 est très proche de la date du render (moins de 5 minutes d'écart), le layer est considéré comme **up-to-date**.
    - Sinon, il est considéré comme **outdated**.
  - Fournit les données nécessaires à l'interface graphique sous forme de dictionnaires imbriqués.

**r_ui.py** :
  - Gère toute l'interface graphique avec Qt (via QtPy).
  - Affiche l'arborescence des séquences, shots et layers, avec filtres dynamiques par statut et par render.
  - Les statuts sont colorés selon leur importance (outdated > missing > up-to-date).
  - Affiche la date de dernière modification des layers dans la popup de détail.
  - Les popups de dépendances sont non-modales et se ferment automatiquement à la fermeture de la fenêtre principale.

**renders_dependency_checker.py** :
  - Point d'entrée du programme.
  - Charge la configuration, appelle le scan des layers et lance l'interface graphique.

## Format du fichier de configuration JSON
Le fichier `config.json` suit la structure suivante :

```json
{
  "layers": [
    "LAYER_A",
    "LAYER_B",
    "LAYER_C"
  ]
}
```