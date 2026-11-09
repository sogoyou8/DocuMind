# DocuMind

**DOC 01 — Plateforme d'intelligence documentaire | D1 : backend local validé**

DocuMind est un projet d'apprentissage professionnel **en cours de développement**. Son ambition est de traiter des documents d'entreprise fictifs (PDF textuels, CSV et XLSX), de structurer les informations dans PostgreSQL, d'orchestrer les traitements avec Airflow et d'offrir une analyse BI et un assistant documentaire IA local.

> **État réel :** D0 documenté et D1 fusionné dans `main` après recette locale du 9 novembre 2026 : 11 tests Django réussis sur PostgreSQL, migrations cohérentes, contrôles OpenAPI stricts et healthcheck OK. Aucun déploiement Render confirmé. Airflow, extraction, Metabase et IA ne sont pas encore implémentés.

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

## Abyss Showcase

- [Fiche DocuMind](https://abyss-public-showcase.vercel.app/projects/documind) — état D0, schémas de conception, boutons **Code source** et **Document**.
- Il n'existe **aucune démo** de l'application à ce stade. Ne pas confondre les schémas pédagogiques avec des captures d'un service exécuté.

## Démonstration

Aucune démonstration publique de l'application complète à ce stade. Le lien de code renvoie au présent dépôt et la fiche Abyss Showcase montre toujours les **intentions et l'architecture D0**. Le backend D1 est validé localement ; D2–D5 restent à développer.

Licence et politique de contribution : à préciser avant publication de la V1.

## D1 — Django REST / PostgreSQL

Le backend et ses tests sont dans `backend/`. Pour une exécution locale, Docker Desktop doit être démarré :

```powershell
docker compose up --build -d
docker compose exec api python manage.py check
docker compose exec api python manage.py test documents -v 2
```

- API : http://127.0.0.1:8000/api/v1/health/ ; documentation : http://127.0.0.1:8000/api/v1/docs/
- Imports locaux uniquement par session authentifiée et rôle `documind_operator` ou administrateur.
- D1 vérifie la nature et la taille des fichiers, pas leur contenu métier (D2).
- PostgreSQL Docker : port hôte `15434`, volume persistant ; ne pas arrêter avec `docker compose down -v`.
- [Contrat de déploiement D0.1](docs/DEPLOIEMENT-D0.1.md) ; [État D1 et validation du 9 novembre](docs/ETAT-D1.md).
- Recette officielle locale : `./scripts/verify-d1.ps1` sous PowerShell avec Docker Desktop.

### Render : coût 0 € et données fictives

`render.yaml` prépare un **Web Service Render gratuit** en lecture seule, sans base PostgreSQL Render (celle-ci expirerait après 30 jours). Trois fiches synthétiques sont réinitialisées sur SQLite éphémère au redémarrage. Le backend local utilise PostgreSQL. Aucune démo complète, aucun hébergement en production ni conservation des données ne sont prétendus tant que les contrôles réels de Render n'ont pas été effectués.
