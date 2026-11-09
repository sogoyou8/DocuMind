# DocuMind — Feuille de route

| Jalons | Mission | Preuve de sortie | État |
|---|---|---|---|
| D0 | Sujet, architecture, UML | Documentation MD/PDF et tests de cohérence | Conception |
| D1 | Django REST + PostgreSQL | Migrations, API OpenAPI et tests sur base réelle | Non commencé |
| D2 | Python/Pandas + Airflow | Imports idempotents, anomalies et tests | Non commencé |
| D3 | SQL métier + Metabase | KPI réconciliés sur données synthétiques | Non commencé |
| D4 | RAG, ChromaDB, Ollama, LangGraph | Citations, abstention, tests d'injection | Non commencé |
| D5 | Intégration, UX, QA et V1.0 | Recette E2E, captures réelles, release | Non commencé |

## Gates
D0->D1 : spécifications et frontières cohérentes.
D1->D2 : backend/migrations/API testés.
D2->D3 : pipeline idempotent, qualité contrôlée.
D3->D4 : métriques réconciliées.
D4->D5 : réponses sourcées et abstention testées.
D5->V1 : tests et démonstration reproductible.

La recherche d'alternance ne dépend pas de la fin de ce projet. Pas de publication publique d'une API ou de démonstration simulée présentée comme réelle.
