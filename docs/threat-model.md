# Modèle de menaces

## Périmètre

Le modèle couvre le chemin entre l'Arduino, la liaison USB série, l'application
de supervision Python et le fichier d'historique local.

Il s'agit d'une analyse pédagogique. Les scénarios décrivent des risques
potentiels, et non la preuve qu'une attaque a réussi.

## Actifs à protéger

- Disponibilité de la supervision.
- Intégrité des mesures affichées.
- Cohérence des états et des alarmes.
- Traçabilité des événements.
- Intégrité et confidentialité du poste de supervision.

## Menaces principales

### T1 — Message JSON malformé

Un flux reçu peut contenir une ligne qui ne peut pas être décodée.

Contrôle existant : décodage JSON et signalement des lignes malformées après
la période de tolérance au démarrage.

Limite : ce contrôle ne prouve pas l'origine du message.

### T2 — Mesure hors limites ou de mauvais type

Une donnée peut dépasser la plage du convertisseur analogique ou présenter
un type inattendu.

Contrôle existant : validation du type entier et de la plage 0 à 1023.

Limite : une valeur dans la plage peut malgré tout être fausse.

### T3 — Incohérence entre mesure et état

Le champ d'état peut contredire la mesure ou les indicateurs d'urgence.

Contrôle existant : vérification de la cohérence des seuils, des états et
des indicateurs d'urgence.

### T4 — Événement inconnu

Un événement non prévu peut être présenté à la supervision.

Contrôle existant : liste d'événements autorisés et signalement des événements
inconnus.

### T5 — Perte de communication

La supervision peut cesser de recevoir des télémétries valides.

Contrôle existant : watchdog et tentative de reconnexion série.

Limite : la détection ne rétablit pas nécessairement la liaison et ne garantit
pas une réaction sûre du procédé physique.

### T6 — Falsification ou rejeu

Un acteur ayant accès au canal pourrait tenter de transmettre des messages
falsifiés ou rejoués.

Contrôle actuel : validation de cohérence applicative uniquement.

Protection manquante : mécanisme cryptographique d'authentification et de
fraîcheur des messages.

### T7 — Altération du journal

Un utilisateur disposant de droits suffisants sur le poste peut modifier
ou supprimer le CSV.

Contrôle actuel : journalisation locale.

Protections à étudier : permissions minimales, sauvegarde, rotation et stockage
centralisé avec contrôle d'accès.

## Priorités recommandées

1. Tester les scénarios de perte et de reprise de communication.
2. Vérifier la journalisation des anomalies en intégration.
3. Protéger le poste et limiter les accès aux fichiers.
4. Concevoir une protection contre la falsification et le rejeu.
5. Définir des procédures de test et de récupération.
