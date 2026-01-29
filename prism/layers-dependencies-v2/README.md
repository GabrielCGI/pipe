# Layers Dependency Checker - Interface de visualisation des dépendances USD

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
- **core.py** :
  - Contient la logique de scan des layers USD et la génération des statuts de chaque layer (up-to-date, outdated, missing, etc.).
  - Fournit les données nécessaires à l'interface graphique sous forme de dictionnaires imbriqués.

- **ui.py** :
  - Gère toute l'interface graphique avec Qt (via QtPy).
  - Affiche l'arborescence des séquences, shots et layers, avec filtres dynamiques par statut et par type de layer.
  - Les statuts sont colorés selon leur importance (outdated > missing > up-to-date > N/A).
  - Affiche la date de dernière modification des layers dans la popup de détail.
  - Les popups de dépendances sont non-modales et se ferment automatiquement à la fermeture de la fenêtre principale.

- **layers_dependency_checker.py** :
  - Point d'entrée du programme.
  - Charge la configuration, appelle le scan des layers et lance l'interface graphique.

## Format du fichier de configuration JSON
Le fichier `config.json` suit la structure suivante :

```json
{
  "LAYER_A": ["LAYER_B", "LAYER_C"],
  "LAYER_B": ["LAYER_D"]
}
```