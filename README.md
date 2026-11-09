# DocuMind

**DOC 01 — Plateforme d'intelligence documentaire | D0 : conception**

DocuMind est un projet d'apprentissage professionnel **en cours de conception**. Son ambition est de traiter des documents d'entreprise fictifs (PDF textuels, CSV et XLSX), de structurer les informations dans PostgreSQL, d'orchestrer les traitements avec Airflow et d'offrir une analyse BI et un assistant documentaire IA local.

> **État réel :** D0 / spécifications. Aucun backend, pipeline, tableau de bord ou assistant IA n'est encore implémenté. Les diagrammes sont des conceptions, pas des captures d'application.

## Périmètre technique envisagé

- **Web / API :** React, TypeScript, Django REST Framework, OpenAPI.
- **Données :** PostgreSQL, Python, Pandas ; extraction PDF textuel et tableaux CSV/XLSX.
- **Orchestration :** Apache Airflow (DAGs, reprise, journalisation).
- **Analytique :** Metabase, indicateurs calculés sur les données structurées.
- **IA locale :** ChromaDB, Ollama et LangGraph pour un RAG avec citations.
- **Qualité :** pytest, tests API, Docker Compose, diagrammes UML.

## Documents de conception

- [Sujet du projet](docs/Sujet-du-projet.md) — énoncé autonome et critères d'acceptation.
- [Architecture](docs/ARCHITECTURE.md) — composants, responsabilités et choix techniques.
- [Modèles UML](docs/UML.md) — diagrammes de classes, séquence et états (Mermaid).
- [Feuille de route](docs/ROADMAP.md) — progression D0 à D5.
- [Validation D0](docs/VALIDATION-D0.md) — décisions et limites vérifiables.
- [Sujet du projet en PDF](docs/Sujet-du-projet.pdf) — version destinée à la lecture et à la fiche Abyss Showcase.

## Conventions

- Données de démonstration **synthétiques, anonymisées ou explicitement autorisées**.
- Aucun service cloud payant ni API LLM distante.
- Les calculs métiers et montants ne sont pas inventés par un modèle génératif.
- Le RAG cite document, page et extrait source, ou signale l'absence de preuve.
- Les traitements lourds restent modulaires ; aucun service n'est supposé opérationnel avant validation.

## Démonstration

Pas de démonstration publique à D0. Le lien de code renvoie au présent dépôt et la fiche Abyss Showcase présente uniquement les **intentions et l'architecture**. D1–D5 seront développés et validés séparément.

Licence et politique de contribution : à définir avant D1.
