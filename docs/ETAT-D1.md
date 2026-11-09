# DocuMind — État du socle D1

## Livré sur `main` (PR #1 fusionnée)
- Modèle `Document` : identifiant UUID, SHA-256, format, état, provenance, fichier privé, horodatage, utilisateur.
- `AuditEvent` : trace d'ajout d'un document.
- API REST : GET `/api/v1/health/`, `/api/v1/overview/`, `/api/v1/documents/`, GET document individuel, POST import authentifié.
- Contrôles fichiers : extensions, signatures PDF/XLSX, CSV UTF-8, taille 5 Mio et doublon SHA-256.
- Démarrage local Compose/PostgreSQL ; mode de démonstration Render gratuit, lecture seule et seed fictif.
- Schéma OpenAPI et interface de documentation.
- Tests Django du socle ; CI configurée avec PostgreSQL 16.

## Non livré à D1
- Parsing métier des factures et données tabulaires (D2).
- Orchestration Airflow (D2).
- Metabase et KPI métiers réconciliés (D3).
- Assistant RAG / Ollama / LangGraph (D4).
- Interface React complète et scénario de démonstration final (D5).

## Commandes de vérification locales
```powershell
docker compose up --build -d
docker compose exec api python manage.py check
docker compose exec api python manage.py makemigrations --check --dry-run
docker compose exec api python manage.py test documents -v 2
```

API locale : http://127.0.0.1:8000 ; les documents locaux exigent l'authentification et le groupe `documind_operator` pour les imports.

**Validation locale : effectuée le 9 novembre 2026.** Le journal fourni de l'exécution `scripts/verify-d1.ps1` confirme les 11 tests, le démarrage de PostgreSQL, l'absence de dérive des migrations, la génération OpenAPI stricte et le healthcheck. Une validation Render distincte a ensuite confirmé que le service est `Live` avec healthcheck HTTP 200.

## OpenAPI : anomalie détectée et correction proposée

Lors de la recette locale du 9 novembre 2026, les 9 tests Django réussissaient, mais la génération OpenAPI émettait 8 erreurs liées à deux vues non annotées (`health`, `overview`). `--validate` seul n'arrêtait pas le script. La branche D1 fournit maintenant des schémas de réponse explicites pour les deux vues, une vérification `--fail-on-warn` bloquante et un test de non-régression. **Correction confirmée dans la recette locale finale : génération OpenAPI stricte réussie.** Le pipeline CI est en déclenchement manuel tant que les quotas Actions sont épuisés.

## Correctif WhiteNoise / Docker (9 novembre 2026)

La recette locale a exposé une course entre la régénération des fichiers statiques au démarrage du conteneur et le scan de WhiteNoise pendant les tests, aggravée par le bind mount `./backend:/app`. Deux tests ont échoué avec `FileNotFoundError` dans `/app/staticfiles/admin/`.

L'image Docker construit désormais les fichiers statiques dans `/opt/documind-staticfiles`, hors du répertoire source monté. Le conteneur ne relance plus `collectstatic` au démarrage. Le script de recette vérifie explicitement la présence des assets stables. **Correction validée par la recette locale finale : tests WhiteNoise et stabilité des fichiers statiques réussis.**

## Clôture de la validation locale D1 — 9 novembre 2026

- Dépôt : `sogoyou8/DocuMind`; PR #1 fusionnée dans `main` (commit `c3bd50d4`).
- Résultat du journal de recette PowerShell : `Ran 11 tests` puis `OK`.
- `python manage.py check` : aucune anomalie.
- `makemigrations --check --dry-run` : aucune différence.
- PostgreSQL Docker : conteneur healthy, création/destruction de la base de test effectuées.
- `spectacular --validate --fail-on-warn` : commande réussie sans avertissement d'outil rapporté.
- `/api/v1/health/` : réponse `ok`; script terminé par `D1 LOCAL OK`.
- **Effectué côté Render** : build Django réussi, migrations et `seed_demo` réussis, Gunicorn en écoute sur le port 10000, déploiement `Live`, healthcheck `GET /api/v1/health/` HTTP 200 répété. **Pas encore effectué depuis un client HTTP externe** : smoke test complet GET docs/overview/catalogue et POST interdit (script dédié ajouté).
- **Hors D1** : pipeline d'extraction/qualité avancée, orchestration Airflow, tableaux Metabase, assistant local.

La réussite est fondée sur le journal d'exécution **local transmis par l'utilisateur** et la vérification des fichiers sur GitHub. GitHub Actions reste manuel et n'est pas une condition de cette validation.

## Déploiement public D1 — 9 novembre 2026

- Service Render : `documind-d1-api-htpg`, ID `srv-dbp0mkugekts73a9t7q0`, **plan `free`** à Francfort, sans ressource de base Render payante.
- URL : https://documind-d1-api-htpg.onrender.com
- Déploiement initial : `dep-dbp0mlugekts73a9targ` ; état remonté par Render : `live` ; build `succeeded`.
- Git : `main`, commit `3c5c9c5` au déploiement initial ; pipeline de déploiement créé depuis `render.yaml`.
- Journaux Render : `Applying documents.0001_initial... OK`, `Three synthetic document metadata examples are available`, `Starting gunicorn 23.0.0`, et plusieurs `GET /api/v1/health/ HTTP/1.1\" 200`.
- Le service ne comporte **aucune base PostgreSQL Render** ; SQLite est éphémère et les trois métadonnées fictives sont réinitialisées au démarrage. PostgreSQL complet est validé **en local**, pas encore hébergé.
- Mode public lecture seule configuré et couvert par le test Django `test_readonly_demo_allows_get_and_blocks_post` ; la recette HTTP externe supplémentaire est décrite dans `scripts/verify-d1-render.ps1`, mais **son exécution extérieure n'est pas vérifiée** à la clôture documentaire.
- Limites : veille du service gratuit, pas d'upload distant, pas de calcul de factures, de pipeline ni d'IA ; données synthétiques seulement.

**Bilan D1 : socle Django REST/PostgreSQL local validé (11/11), backend public Render Free fonctionnel et healthcheck validé. La recette HTTP externe complète reste une vérification complémentaire, non une preuve déjà acquise.**
