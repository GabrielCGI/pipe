# Alerte de température

L'idée est de se connecter aux détecteurs de température présents dans les 
différentes pièces du studios et d'envoyer une notification sur discord en 
cas de température trop élevéee.

## Requirements
Les packages sont dans les dossiers `.venv/Lib/site-packages`. 

Python packages:
 - discord_webhook
 - python-xsense
 - aiohttp

## Fonctionnement

Les différents capteurs sont de la marque XSense, il faut donc envoyé des 
requête au compte XSense de Illogic. Pour cela, nous utilisons un API 
développée en Python par un indépendant :
[https://github.com/theosnel/python-xsense/tree/0.0.14]

Ensuite, à l'aide de WebHook discord, on envoie l'alerte sur discord.

La tâche est plannifiée toutes les 5 minutes sur `MOTHER`.

## Planification

Il s'agit d'une tâche dans le plannificateur de tâche de `MOTHER` qui se relance toutes les 5 minutes.
Le script `alarm.py` permet l'appel à l'API et l'envoie de messages discord.
Les scripts `check_temperature.bat` et `invis.vbs` servent à lancer ce script Python silencieusement
avec `wscript.exe`.
Ces deux scripts sont directement situé dans `MOTHER` dans `C:\Tasks\TemperatureAlert`