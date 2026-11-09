# DocuMind — Revue de conception D0

Date : 9 novembre 2026.

## Décisions figées pour D0
- Projet indépendant des autres applications ABYSS.
- Objectif éducatif et démonstrable : Full Stack, Data Engineering, BI, IA locale.
- V1 : fichiers PDF textuels, CSV, XLSX fictifs ou autorisés.
- Stack : React/TypeScript, Django REST, PostgreSQL, Pandas, Airflow, Metabase, ChromaDB, Ollama, LangGraph.
- AWS et API IA payantes exclus.
- 32 Go de RAM sur le PC de travail ; services modulaires.
- KPI déterministes ; RAG sourcé et abstention.
- La fiche Abyss Showcase présente **D0, pas une application déjà développée**.

## Contrôles de conception
- [x] Sujet autonome : contexte, mission, contraintes, fonctionnalités, validation.
- [x] Architecture et séparation des responsabilités.
- [x] UML : composants, classes, séquence, états.
- [x] Roadmap D0 à D5, jalons et conditions de passage.
- [x] Politique de données synthétiques et de non-exfiltration.
- [ ] Vérification d'exécution du logiciel : prévue en D1-D5.
- [ ] Captures authentiques d'interface : aucune en D0.

## Risques
- Charge Airflow/Metabase/Ollama : démarrer séparément, mesurer.
- Données malveillantes : formats bornés, scan/validation, stockage privé.
- Hallucinations : séparer SQL et LLM, vérifier citations et abstention.
- Duplications : clés de provenance et rejouabilité idempotente.
- Confusion entre concept et produit livré : statut « En développement » et diagrammes explicitement pédagogiques.

**Décision : D0 documenté. D1 reste à implémenter et valider.**
