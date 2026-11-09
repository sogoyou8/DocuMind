# DocuMind — Architecture cible D0

**Statut : conception.** Aucun service opérationnel n'est supposé.

## Composants et responsabilités
1. **React/TypeScript** : interface d'import, catalogue, détails, suivi, tableaux de bord et assistant.
2. **Django REST Framework** : authentification, permissions, validation, API et audit des actions.
3. **PostgreSQL** : source de vérité de documents, événements, extractions, anomalies, fournisseurs, factures et agrégats.
4. **Worker Pandas/Python** : lectures PDF textuelles, CSV/XLSX, normalisation et contrôles déterministes.
5. **Airflow** : déclenchement des traitements, dépendances, retries et visibilité des exécutions.
6. **Metabase** : lecture de vues SQL filtrées, jamais accès direct aux uploads bruts.
7. **ChromaDB** : index d'extraits documentaires avec page, source, version et référence.
8. **LangGraph/Ollama** : recherche de contexte et formulation locale sourcée ; sans accès libre aux commandes ou aux mutations SQL.

## Flux métier
Import UI -> API -> dépôt privé et Document/ProcessingRun (RECEIVED) -> Airflow -> worker -> validation -> PostgreSQL (ACCEPTED/REJECTED) -> index (INDEXED) -> Metabase et assistant.

## Invariants de cohérence
- Clé d'idempotence : document, version du pipeline, identifiant de ligne source.
- Historiser les transitions et raisons d'échec sans effacer les traces anciennes.
- Exclure les lignes non validées des vues de reporting.
- Calculer les KPI en SQL/Pandas et non par génération libre.
- Le moteur RAG cite les sources ou s'abstient ; ses documents sont des entrées non fiables.
- La V1 n'expose aucun upload ni secret depuis le frontend.

## Organisation des services
Profils Compose : core (Django/PostgreSQL), pipeline (Airflow/worker), analytics (Metabase), ai (ChromaDB/Ollama/LangGraph). Un démarrage séquentiel convient au poste de travail. Le modèle local sera choisi après mesure de la consommation RAM/CPU.

## À définir lors de D1
Bibliothèque PDF, gestion des comptes, migration SQL, limites d'import testées, politique de rétention, format exact du corpus et mécanismes de stockage.

## État réel à D2 (branche `work/d2-pandas-airflow`)

Le stockage PostgreSQL et le backend D1 sont déjà validés localement ; le backend D1 Render Free est Live. Le moteur `documents.pipeline` implémente extraction PDF/CSV/XLSX, normalisation déterministe et contrôles transactionnels en local. Le document verrouillé en base garantit l'idempotence des versions sur PostgreSQL. Les enregistrements bruts, positions sources et anomalies sont historisés dans les tables dédiées. Les factures d'un fichier rejeté ne sont jamais insérées.

La base et l'API tournent avec le Compose principal. Airflow 3.4 est isolé derrière `--profile pipeline`, utilise un volume de métadonnées propre et partage l'accès **en lecture seule** aux imports locaux du backend. Son DAG planifié toutes les six heures utilise la même commande `process_pending` que la recette : pas de duplication des règles métier.

**À ne pas confondre** : le composant Render Free est uniquement la démo D1 en lecture seule avec SQLite jetable. Les traitements D2 ne sont pas exécutés en ligne. La validation effective du DAG et du traitement local doit être confirmée par `scripts/verify-d2.ps1` avant fusion D2.
