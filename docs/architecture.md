# Architecture du mini-SCADA

## 1. Couche terrain

L'Arduino Uno représente la couche terrain du laboratoire. Il acquiert une
mesure du capteur de niveau d'eau et applique la logique d'état et d'alarme
implémentée dans le firmware.

Les mesures sont transmises à l'application de supervision au format JSON.

## 2. Communication

La liaison USB série utilise actuellement 9600 bauds. Le logiciel Python
écoute le port configuré dans `scada.py`.

Le worker série gère les tentatives de reconnexion. Les données reçues sont
décodées puis soumises aux contrôles applicatifs.

La liaison série n'est pas un canal cryptographiquement authentifié.

## 3. Supervision

L'interface Python/Tkinter présente les mesures, les états, les alarmes et
l'état de la communication.

La fonction `validate_telemetry()` contrôle notamment :

- le type de message ;
- l'identifiant du capteur ;
- la plage de mesure 0 à 1023 ;
- les seuils configurés ;
- les types des champs booléens ;
- la cohérence entre mesure, état et urgence.

La fonction `handle_data()` distribue les télémétries valides et les événements
autorisés. Les données incohérentes sont traitées comme des anomalies.

## 4. Surveillance de communication

Le watchdog utilise un délai configuré de cinq secondes. Il signale une
communication perdue lorsque les télémétries valides ne sont plus reçues dans
le délai prévu.

Le worker tente de rétablir la liaison lorsque le port série est indisponible.

## 5. Journalisation

La fonction `write_log()` ajoute les mesures et événements à
`scada_history.csv`. Le journal permet d'examiner les états successifs et les
incidents observés pendant les essais.

Le CSV n'est ni une base de données transactionnelle ni un journal inviolable.

## 6. Limites

Le système ne met pas en œuvre, à ce stade, une authentification cryptographique
des messages, une protection cryptographique contre le rejeu, ou une
architecture de sécurité réseau industrielle complète.
