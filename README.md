# DocuMind

**DOC 01 — Plateforme d'intelligence documentaire | D1 validé · D2 Python/Pandas + Airflow en cours de recette**

DocuMind est un projet d'apprentissage professionnel **en cours de développement**. Son ambition est de traiter des documents d'entreprise fictifs (PDF textuels, CSV et XLSX), de structurer les informations dans PostgreSQL, d'orchestrer les traitements avec Airflow et d'offrir une analyse BI et un assistant documentaire IA local.

> **État réel :** D0 documenté et D1 fusionné dans `main` après recette locale du 9 novembre 2026 : 11 tests Django réussis sur PostgreSQL, migrations cohérentes, contrôles OpenAPI stricts et healthcheck OK. Déploiement Render gratuit **Live** le 9 novembre 2026 : migrations et initialisation de 3 exemples synthétiques réussies, service Gunicorn en ligne et healthcheck HTTP 200. L'API reste en lecture seule sur Render ; pas de base PostgreSQL hébergée ni de frais engagés. **D2 en branche de travail : extraction Pandas/PDF/XLSX, qualité, factures PostgreSQL et DAG Airflow local implémentés, mais non encore validés sur Docker**. Metabase et IA ne sont pas encore implémentés.

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
- Le socle backend D1 fonctionne sur Render, mais **aucune démo visuelle du produit Full Stack V1 n'existe encore**. Les schémas de la fiche restent des conceptions, pas des captures d'une application complète.

## Démonstration

Une **prévisualisation publique du socle backend D1** existe sur Render, mais aucune démonstration de l'application Full Stack complète à ce stade. Le lien de code renvoie au présent dépôt et la fiche Abyss Showcase montre toujours les **intentions et l'architecture D0**. Le backend D1 est validé localement ; D2 se développe sur `work/d2-pandas-airflow`, sans fusion tant que la recette locale complète ne passe pas. D3–D5 restent à développer.

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

**Service actuellement déployé :** [DocuMind D1 API](https://documind-d1-api-htpg.onrender.com) (Render Web Service Free, région Francfort), via `render.yaml`. Render confirme un déploiement `Live`, les migrations Django et le healthcheck `GET /api/v1/health/` HTTP 200. Le mode public `DOCUMIND_DEMO_READONLY=1` expose trois **fiches fictives** stockées sur SQLite éphémère ; il n'autorise pas les imports publics. Le backend local, lui, utilise PostgreSQL. Le déploiement n'embarque ni Airflow, ni Metabase, ni Ollama. Il ne garantit pas la persistance des données ni la disponibilité 24/7. Les autres routes ont été couvertes par les tests Django locaux ; un smoke test HTTP public complémentaire reste disponible.


### Recette HTTP de la démo Render

En PowerShell : `./scripts/verify-d1-render.ps1`. Ce script contrôle les routes publiques, les trois exemples synthétiques et l'interdiction d'écriture via un POST non authentifié. Un éventuel sommeil de l'instance Render Free peut ralentir la première requête. **La preuve d'exécution de ce script depuis l'extérieur n'est pas encore enregistrée dans le dépôt.**

## D2 — Traitement documentaire déterministe (en cours de validation)

Le pipeline D2 utilise **Pandas, openpyxl et pypdf** en local. Il extrait les tables CSV/XLSX ou les pages d'un PDF textuel, normalise les champs requis des factures (fournisseur, numéro, date, devise, HT, TVA, TTC), conserve la provenance et les anomalies, puis produit uniquement les factures acceptées. Les documents incohérents sont mis en quarantaine sans contribuer aux indicateurs. La reprise est idempotente par document/version.

- Commandes : `python manage.py seed_d2 --process`, `process_pending`, `verify_d2`.
- API locale : `POST /api/v1/documents/{id}/process/`, `GET /api/v1/invoices/`, `/processing-runs/`, `/records/`, `/quality-issues/`.
- Airflow local facultatif au quotidien, **obligatoire à la recette D2 complète**, via `docker compose --profile pipeline up -d airflow`. Interface Airflow sur http://127.0.0.1:8088.
- Recette complète PowerShell : `.\scripts\verify-d2.ps1`, en conservant les volumes PostgreSQL. Le script inclut les tests existants et une exécution du vrai DAG Airflow.
- Corpus entièrement fictif et reproductible : 3 factures acceptées, 1 document rejeté ; montant validé attendu 240,00 EUR TTC (aucun montant inventé).
- Documentation : [État et recette D2](docs/ETAT-D2.md).

**Important :** la branche D2 n'est pas encore fusionnée ; ses tests sur Docker/Airflow doivent réussir avant de déclarer le lot terminé. Le Web Service Render Free reste celui de D1, en lecture seule, sans import ni Airflow hébergé.
