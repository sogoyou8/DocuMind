# DocuMind — D2 : extraction déterministe, qualité et orchestration locale

## Objectif
Traiter **réellement** des imports déjà reçus par D1 (PDF textuel, CSV UTF-8, classeurs XLSX sans macros), convertir des factures structurées, conserver leur provenance et **refuser tout document incorrect** sans contaminer les futurs KPI.

## Architecture D2
1. `documents.pipeline.extraction` : extraction bornée des PDF (pypdf), CSV (Pandas), XLSX (openpyxl lecture seule et Pandas), provenance `pdf:page:N`, `csv:record:N`, `xlsx:Feuille:row:N`.
2. `documents.pipeline.normalization` : mapping d'alias explicites, dates, devises et montants `Decimal`. Aucun chiffre, champ ni fournisseur n'est inféré par IA.
3. `documents.pipeline.runner.process_document` : transactions PostgreSQL et verrouillage des documents, idempotence `document + d2-v1`, rejeu explicite avec `force=true`, contrôles d'empreinte et de doublons.
4. Modèles `ProcessingRun`, `ExtractedRecord`, `QualityIssue`, `Supplier`, `Invoice`. Les documents avec anomalie passent en `REJECTED` et **aucune facture de ce document** n'entre dans la table des factures acceptées.
5. `process_pending` : commande autonome limitée à 50 documents par lot. `seed_d2` : corpus de quatre documents fictifs reproductibles. `verify_d2` : assertions SQL sur le corpus.
6. Airflow 3.4.0 : DAG local `documind_d2_ingestion`, planifié toutes les six heures, tâche Python qui appelle le même moteur Django idempotent, avec reprises. Image indépendante, démarrée via le profil Compose `pipeline`.

## API locale
- `POST /api/v1/documents/{uuid}/process/` — opérateur/admin seulement. Corps `{"force": true}` pour rejouer.
- `GET /api/v1/processing-runs/?document={uuid}` — statut, tentative, dates.
- `GET /api/v1/records/?document={uuid}` — données brutes, normalisées et emplacement source.
- `GET /api/v1/quality-issues/?document={uuid}` — anomalies et champs.
- `GET /api/v1/invoices/?document={uuid}` — uniquement les factures validées, avec fournisseur et montants.

Les endpoints de consultation locaux nécessitent une authentification. Le serveur public Render conserve le mode `DOCUMIND_DEMO_READONLY=1` : **aucun traitement, aucun import public, aucune donnée D2 exposée**. La base de l'application complète reste PostgreSQL local.

## Règles et limites explicites
- CSV : UTF-8, jusqu'à 5 000 enregistrements, 40 colonnes.
- Excel : 10 feuilles, 5 000 enregistrements cumulés, 40 colonnes, valeurs calculées disponibles uniquement ; pas de macros ni d'exécution de formules.
- PDF : 20 pages et 200 000 caractères extraits au maximum, **texte natif uniquement**, 1 facture attendue par page, lignes de métadonnées de type `Nom: valeur`. Pas d'OCR.
- Source : 5 Mio maximum ; la taille et le SHA-256 de l'import sont revérifiés avant traitement.
- Facture : fournisseur, numéro, date, devise, HT, TVA, TTC exigés. Devises EUR, USD ou GBP. Montants non négatifs et `HT + TVA = TTC` à 0,01 près.
- Modèle volontairement strict : un fichier contenant une ligne erronée est **rejeté dans son entier**. Les enregistrements bruts et diagnostics restent consultables ; aucun montant rejeté n'alimente D3.
- Les replays sans `force` réutilisent le résultat existant et ne dupliquent pas les factures. Les replays forcés recalculent la même version `d2-v1` et conservent un audit de la décision.
- Les PDF « libres » sans structure explicite peuvent être rejetés : ce lot n'inclut pas l'IA d'extraction ni l'OCR.

## Validation locale (Windows PowerShell + Docker Desktop)
Sur la branche D2 :
```powershell
.\scripts\verify-d2.ps1
```
Ce script vérifie D1 + D2 sur PostgreSQL, crée les quatre fichiers **fictifs**, réalise le traitement et son rejeu, contrôle exactement **3 documents ACCEPTED / 1 REJECTED**, trois factures acceptées pour **240,00 EUR TTC**, puis construit, démarre et exécute le DAG Airflow.

Un lancement plus léger `.\scripts\verify-d2.ps1 -SkipAirflow` teste les transformations et PostgreSQL, mais **ne valide pas Airflow**.

Airflow UI locale : `http://127.0.0.1:8088` ; l'identifiant administrateur et le mot de passe générés sont visibles dans les journaux Airflow locaux, à ne jamais publier. Le service peut être arrêté avec `docker compose --profile pipeline stop airflow`. **Ne pas utiliser `docker compose down -v`** : cela détruirait les volumes de base et d'Airflow.

## État de vérification
Code D2 sur branche `work/d2-pandas-airflow`, tests ajoutés et script de recette disponible. La réussite de ces tests et du DAG dans l'environnement Docker de l'utilisateur doit être **observée** avant de fusionner la branche ou d'affirmer D2 validé. Les quotas GitHub Actions étant épuisés, la validation locale remplace la CI distante.

## Hors D2
- Metabase, réconciliation BI et vues SQL analytiques : D3.
- ChromaDB, Ollama, LangGraph, citations RAG : D4.
- Interface React complète et démonstration utilisateur finale : D5.
