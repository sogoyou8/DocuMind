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

## État réel à D2 (validé localement le 9 novembre 2026)

Le stockage PostgreSQL et le backend D1 sont déjà validés localement ; le backend D1 Render Free est Live. Le moteur `documents.pipeline` implémente extraction PDF/CSV/XLSX, normalisation déterministe et contrôles transactionnels en local. Le document verrouillé en base garantit l'idempotence des versions sur PostgreSQL. Les enregistrements bruts, positions sources et anomalies sont historisés dans les tables dédiées. Les factures d'un fichier rejeté ne sont jamais insérées.

La base et l'API tournent avec le Compose principal. Airflow 3.4 est isolé derrière `--profile pipeline`, utilise un volume de métadonnées propre et partage l'accès **en lecture seule** aux imports locaux du backend. Son DAG planifié toutes les six heures utilise la même commande `process_pending` que la recette : pas de duplication des règles métier.

**À ne pas confondre** : le composant Render Free est uniquement la démo D1 en lecture seule avec SQLite jetable. Les traitements D2 ne sont pas exécutés en ligne. La recette `scripts/verify-d2.ps1` a reussi avec 30 tests PostgreSQL et un DagRun Airflow en etat `success`. Le DagRun validait le worker sans document en attente, le corpus ayant deja ete entierement traite. Render conserve la demonstration D1 en lecture seule.

## État D3 — BI PostgreSQL et Metabase local

D3 ajoute le schéma SQL `bi` (neuf vues PostgreSQL) séparé des données opérationnelles D2. Toutes les sommes proviennent des factures dont le document est `ACCEPTED` ou `INDEXED` **et** dont le traitement est `SUCCEEDED`. Les anomalies et les données rejetées n'alimentent pas les totaux. La date utilisée pour les dépenses mensuelles est la date de facture, jamais celle d'import. Les sommes sont séparées par devise.

Metabase Open Source (profil Docker `analytics`) lit uniquement les vues `bi` via le rôle `documind_bi` à privilèges restreints. Un compte admin Metabase existe localement pour créer les questions et dashboard. Les secrets restent sous `data/local/`, ignorés par Git. La base de configuration H2 persiste dans un volume local, **non appropriée à la production**.

Le mode Render Free garde son backend Django + SQLite éphémère, en lecture seule : la migration D3 vérifie la nature PostgreSQL avant de créer des vues. **Aucun Metabase public et aucune facture privée sur Render.**

La recette complète D3 du 9 novembre 2026 a validé **36 tests Django/PostgreSQL**, l'accès SQL limité au schéma BI, les **12 questions SQL réellement exécutées par Metabase**, et la réconciliation des sommes mensuelles/fournisseurs/devises. Voir [ETAT-D3.md](ETAT-D3.md) pour les preuves et limites. Cette validation ne constitue pas encore une revue visuelle UX de Metabase ; aucun Metabase n'est déployé publiquement.
