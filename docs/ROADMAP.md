# DocuMind — Feuille de route

| Jalons | Mission | Preuve de sortie | État |
|---|---|---|---|
| D0 | Sujet, architecture, UML | Documentation MD/PDF et tests de cohérence | Terminé |
| D1 | Django REST + PostgreSQL | 11 tests locaux sur PostgreSQL + Render Free Live | Validé (9 nov. 2026) |
| D2 | Python/Pandas + Airflow | 30 tests reussis, 3 acceptes/1 rejete, 240 EUR TTC, rejeu sans doublons et DagRun Airflow `success` | Valide localement (9 nov. 2026) |
| D3 | SQL métier + Metabase | 36/36 tests, 9 vues BI, rôle SELECT seul, 12 questions Metabase réconciliées, `D3 LOCAL OK` | Validé localement (9 nov. 2026) |
| D4 | RAG, ChromaDB, Ollama, LangGraph | Index document/ligne, citations vérifiables, abstention et tests réels Ollama/Chroma | Implémenté sur branche, recette locale à vérifier |
| D5 | Intégration, UX, QA et V1.0 | Recette E2E, captures réelles, release | Non commencé |

## Gates
D0->D1 : spécifications et frontières cohérentes.
D1->D2 : backend/migrations/API testés.
D2->D3 : pipeline idempotent, qualité contrôlée.
D3->D4 : métriques réconciliées.
D4->D5 : réponses sourcées et abstention testées.
D5->V1 : tests et démonstration reproductible.

La recherche d'alternance ne dépend pas de la fin de ce projet. Un backend Render Free D1, en lecture seule et avec exemples fictifs, est public ; aucun pipeline D2 ni service lourd n'est hébergé. Les modules non fonctionnels ne sont jamais présentés comme opérationnels.
