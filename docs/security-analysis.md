# Analyse de sécurité et résultats

## Contrôles implémentés

Le code actuel comporte :

- validation des télémétries JSON ;
- contrôle de la plage de mesure ;
- vérification de la cohérence des états et urgences ;
- liste d'événements autorisés ;
- détection des lignes JSON malformées ;
- surveillance de la fraîcheur des télémétries ;
- reconnexion série automatique ;
- journalisation CSV des mesures et événements.

## Tests automatisés

Les tests du projet examinent plusieurs catégories :

- messages valides et invalides ;
- mesures hors plage ;
- états et indicateurs d'urgence incohérents ;
- événements autorisés et inconnus ;
- écriture et ajout de lignes CSV sur des fichiers temporaires.

Les tests unitaires des fonctions extraites vérifient la logique de ces fonctions.
Ils ne remplacent pas des essais de bout en bout sur le matériel réel.

## Interprétation

Une validation syntaxique et sémantique réduit les erreurs de traitement,
mais ne garantit pas l'authenticité des données.

Un watchdog aide à détecter une absence de télémétrie, mais ne constitue pas
à lui seul un mécanisme de sécurité fonctionnelle.

Une journalisation locale facilite l'analyse des incidents, mais ne garantit
pas l'intégrité du journal face à un acteur ayant les droits d'écriture.

## Travaux futurs

- Ajouter des tests d'intégration du traitement des messages.
- Simuler la perte puis le rétablissement de communication dans un environnement
  isolé.
- Tester les erreurs d'écriture du journal.
- Concevoir une protection cryptographique contre la falsification et le rejeu.
- Documenter les résultats réels de chaque essai avec date, procédure et sortie.
- Évaluer les mesures de sécurité supplémentaires dans un environnement OT
  de laboratoire.

## Conclusion

Le projet constitue une base pédagogique pour étudier l'acquisition terrain,
la supervision, la validation des données, la disponibilité de communication
et la traçabilité des événements. Il ne doit pas être présenté comme un système
certifié ou comme une protection complète contre les attaques OT.
