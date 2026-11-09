# DocuMind — État du socle D1

## Livré sur branche de travail
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

**Attention :** l'existence des tests et de la CI ne constitue pas une validation d'exécution. Seuls leurs résultats effectifs permettront de marquer D1 « validé ».
