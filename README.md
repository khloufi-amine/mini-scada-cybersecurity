# Industrial Cybersecurity Testbed — Mini-SCADA

## Présentation

Laboratoire pédagogique associant automatisme, supervision et cybersécurité
des systèmes industriels (OT).

Le projet repose sur un Arduino Uno qui acquiert une mesure de niveau d'eau
et transmet sa télémétrie à une application SCADA Python sur PC.

La supervision affiche les mesures et les états du système, détecte plusieurs
anomalies de données et surveille la disponibilité de la communication série.

## Objectifs

- Acquérir et superviser une mesure provenant d'un système physique.
- Transmettre les données au format JSON via USB série.
- Détecter les messages malformés ou incohérents.
- Surveiller la fraîcheur des mesures et les pertes de communication.
- Journaliser les mesures et événements dans un fichier CSV.
- Tester les règles de validation et les fonctions de journalisation.

## Architecture

```text
+-----------------------------+
| Arduino Uno                 |
| Capteur de niveau d'eau     |
| Logique locale et alarmes   |
+--------------+--------------+
               |
               | USB / série
               | JSON, 9600 bauds
               v
+-----------------------------+
| PC Windows                  |
| Python / Tkinter            |
|                             |
| - Réception des données     |
| - Validation des messages   |
| - Surveillance communication|
| - Détection d'anomalies     |
+--------------+--------------+
               |
               v
+-----------------------------+
| scada_history.csv           |
| Mesures et événements       |
+-----------------------------+
```

## Technologies

- Arduino Uno et firmware embarqué
- Python 3
- Tkinter
- PySerial
- JSON
- CSV
- unittest
- PowerShell

## Prérequis

- Windows
- Python installé et accessible via `py`
- Arduino connecté au PC
- Port série correctement configuré dans `scada.py`
- Bibliothèque Python `pyserial`

Installation de la dépendance :

```powershell
py -m pip install pyserial
```

## Lancement

Depuis le dossier du projet :

```powershell
py .\scada.py
```

Le port série configuré actuellement dans le code est `COM10`, avec un débit
de 9600 bauds. Adapter le port si nécessaire.

## Tests

Les fichiers de tests présents dans le projet couvrent notamment :

- la validation de télémétries normales, d'avertissement et critiques ;
- le rejet de mesures hors limites ;
- le rejet de champs incohérents ;
- le routage d'événements autorisés et inconnus ;
- la journalisation CSV sur des fichiers temporaires.

Exécution de la suite :

```powershell
py -m unittest -v test_security.py test_incidents.py test_real_validation.py test_csv_logging.py test_event_handling.py
```

Les tests unitaires ne constituent pas à eux seuls une validation complète
de bout en bout du système physique.

## Limites de sécurité

Ce projet est un laboratoire pédagogique et non un système industriel certifié.

La liaison USB série n'apporte pas, à elle seule, de chiffrement ou
d'authentification cryptographique des messages. La validation des données
ne garantit pas leur authenticité.

Le watchdog détecte une absence de télémétrie valide au-delà du délai configuré,
mais ne garantit pas la disponibilité du système.

Les tests automatisés doivent être complétés par des essais d'intégration
contrôlés et documentés.

## Pistes d'amélioration

- Ajouter un identifiant de séquence et une détection de rejeu.
- Authentifier les messages avec un mécanisme cryptographique adapté.
- Ajouter des tests d'intégration reproductibles.
- Définir une politique de conservation et de rotation des journaux.
- Documenter les scénarios de défaillance et les mesures correctives.
- Étudier la segmentation réseau et la supervision de sécurité OT dans un
  environnement de laboratoire adapté.

## Structure actuelle

```text
mini_scada/
├── scada.py
├── scada_history.csv
├── test_security.py
├── test_incidents.py
├── test_real_validation.py
├── test_csv_logging.py
├── test_event_handling.py
├── scada_backup_phase37.py
└── docs/
    ├── architecture.md
    ├── threat-model.md
    └── security-analysis.md
```

L'historique CSV et la sauvegarde sont des fichiers locaux de travail.
Ne pas publier de données personnelles ou de journaux contenant des informations
sensibles.
