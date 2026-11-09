# DocuMind D4 — Assistant documentaire IA local, citations et abstention

## Mission

D4 transforme les **lignes CSV/XLSX ou pages PDF textuelles validées par D2** en passages recherchables localement, puis permet à un utilisateur authentifié de poser des questions avec des références vérifiables. Aucun modèle, fichier ni texte de facture n'est transmis à une API IA externe.

**État : D4 validé localement le 9 novembre 2026** sur Docker Desktop, avec les vrais modèles Ollama et ChromaDB, après réussite complète des tests. Fusion GitHub et vérification Render sont des étapes distinctes.

## Architecture réelle

`Document (ACCEPTED)` → `ProcessingRun (SUCCEEDED)` → `ExtractedRecord` → `documents.rag.sources` (passages bornés, page/ligne conservée) → `LocalOllama /api/embed` (`nomic-embed-text`) → `ChromaDB PersistentClient` (volume Docker privé) → `ChunkReference` (PostgreSQL, SHA-256 du texte, modèle, run et localisateur) → `Document INDEXED`.

Requête utilisateur → route Django REST authentifiée → **LangGraph** : retrieval Chroma, revérification PostgreSQL et SHA-256, filtrage des passages qui contiennent des instructions hostiles, abstention si aucun élément suffisant, sinon `Ollama /api/generate` (`qwen2.5:1.5b`) → validation des identifiants de citations et des nombres présents dans les passages → réponse ou abstention.

Les extraits bruts sont dans Chroma local ; les seules métadonnées de référence sont dans PostgreSQL. Les identifiants de citations renvoyés à l'utilisateur sont décidés par le serveur à partir des enregistrements autorisés, pas par le modèle.

### Services et coûts

- **Backend Django classique** : `127.0.0.1:8000`, inchangé ; PostgreSQL local : `15434`.
- **API RAG optionnelle** : `127.0.0.1:8001`, profil `ai`, image `Dockerfile.rag` avec ChromaDB et LangGraph.
- **Ollama local** : `127.0.0.1:11435`, image `ollama/ollama:0.12.11` ; modèle d'embedding `nomic-embed-text` et modèle de génération compact `qwen2.5:1.5b`.
- **ChromaDB embedded** : volume `documind_chroma_state`, **aucun port Chroma public**. Modèles Ollama : volume `documind_ollama_models`.
- **Render Free** : uniquement la démo D1 en lecture seule. L'option `DOCUMIND_AI_ENABLED` est désactivée sur Render et forcée à `false` lorsque `DOCUMIND_DEMO_READONLY=1`. Aucun hébergement IA, aucune base vectorielle hébergée et **aucun abonnement payant**.

Après la recette, arrêter les services lourds sans supprimer leurs données : `docker compose --profile ai stop rag ollama`. **Jamais `docker compose down -v`**, qui détruirait notamment la base PostgreSQL et les volumes IA.

## API locale

- `POST http://127.0.0.1:8001/api/v1/documents/{uuid}/index/` : opérateur/admin, indexe un document accepté. Rejouable, sans créer de nouveaux extraits si la version est déjà complète ; si le volume Chroma est perdu, l'index est reconstruit.
- `POST http://127.0.0.1:8001/api/v1/assistant/ask/` : utilisateur authentifié (opérateur/analyste/admin), JSON `{"question":"Quel est le montant TTC de DM-2026-001 ?"}`. Réponse `{"status":"answered","answer":"...","citations":[{"id":"E1","document_id":"uuid","document":"nom.csv","source_locator":"csv:record:1","excerpt":"..."}]}` ou `{"status":"abstained","answer":"Je ne trouve pas de preuve suffisante dans les documents validés pour répondre.","citations":[]}`.
- `GET http://127.0.0.1:8001/api/v1/assistant/status/` : utilisateur authentifié, indique le mode local, modèles configurés et quantité de passages ; ce statut n'est pas une mesure de qualité des réponses.
- `python manage.py index_pending --limit 20` : lot local borné ; `python manage.py verify_d4` : tests réels Ollama/Chroma/LangGraph sur le corpus fictif.

**Les factures rejetées n'entrent jamais dans l'index.** Les anciens vecteurs Chroma non référencés en SQL, les documents retirés, les runs rejetés et les contenus dont l'empreinte ne correspond plus sont tous exclus de la recherche.

## Sécurité / limites explicites

1. Authentification et permissions côté Django. Les POST d'indexation nécessitent le rôle `documind_operator` ou administrateur ; les questions sont limitées à **10/min par utilisateur**.
2. Les documents et questions sont des **données non fiables**. Ils ne sont jamais autorisés à fournir des instructions système, appels d'outils ou paramètres SQL à l'assistant ; le graphe n'a **aucun accès** aux commandes shell, à l'API de modification PostgreSQL ni à des services cloud.
3. Filtre de motifs connus d'injection (`ignore previous instructions`, rôles simulés, demande de secrets, etc.). Une détection par motifs **n'est pas une garantie contre toutes les attaques** ; la sortie est également contrôlée.
4. Une source absente ou une facture identifiée inconnue provoque une abstention. Le modèle doit citer des extraits admis par PostgreSQL et l'empreinte SHA-256 ; le serveur rejette citations et nombres inconnus. **Cela réduit les hallucinations, sans démontrer l'exactitude de toute phrase produite par un LLM.**
5. Les agrégats financiers multi-documents doivent être calculés par **D3 SQL**, pas en additionnant librement les sorties d'un petit modèle.
6. Les données citées (noms, références, passages) restent **locales et potentiellement sensibles** : n'utiliser que des documents fictifs ou autorisés, ne jamais publier `documind_chroma_state`, les volumes Ollama ni des sorties brutes privées.
7. Le PDF textuel reste limité aux pages que D2 peut réellement extraire ; ni OCR, ni pages scannées, ni RAG distant, ni entraînement de modèles.

## Validation

Recette intégrale Windows PowerShell (Docker Desktop en service, branche D4) :

```powershell
.\scripts\verify-d4.ps1
```

Le script :
1. exécute les tests Django D1/D2/D3 existants avec migration D4 et OpenAPI, et valide le corpus D3 ;
2. exécute le précontrôle de syntaxe et des barrières locales ;
3. arrête **sans supprimer les volumes** Metabase et Airflow pour libérer de la mémoire ;
4. démarre Ollama et télécharge ses **deux modèles gratuits** dans son volume Docker (premier téléchargement seulement) ;
5. construit et démarre le backend `rag` local uniquement ;
6. exécute tous les tests, y compris les scénarios D4 simulés, et contrôle migrations et OpenAPI ;
7. indexe les documents validés puis rejoue le processus et interroge les **vrais modèles** sur une facture connue, une facture inconnue et une instruction malveillante ;
8. vérifie que les **1 344,00 EUR** du corpus synthétique D3 restent exacts après l'indexation.

**Preuve finale obtenue : `D4 LOCAL OK`.** Le script a exécuté les 10 tests D4 dans le conteneur IA, puis testé les vrais modèles Ollama/Chroma/LangGraph. Les réponses générées restent à contrôler individuellement : les tests ne garantissent pas l'exactitude universelle du LLM.

Un lancement `-SkipCoreTests` accélère une nouvelle tentative **après** validation des régressions ; il ne constitue pas une recette initiale suffisante.

## Hors D4

L'interface React/TypeScript, le cockpit mono-écran et la release V1.0 de DocuMind sont prévus en **D5**. Le service RAG local expose des routes API réelles, **pas encore une interface utilisateur finale**.

## Preuves de recette du 9 novembre 2026

- Précontrôle `D4 STATIC OK`, migrations `documents.0001` à `0004`, absence de migration manquante.
- Première étape sur le backend standard : `Ran 47 tests ... OK (skipped=10)` ; les dix tests D4 sont volontairement désactivés sans l'environnement IA.
- Téléchargement réel d'Ollama 0.12.11, des modèles `nomic-embed-text` et `qwen2.5:1.5b`, puis construction et démarrage de `documind-rag`.
- **Deuxième étape dans le service RAG : `Ran 47 tests ... OK` sans saut**, couvrant l'indexation, les permissions, l'intégrité des sources, les fausses citations, les injections et l'abstention.
- `D4 indexed_documents=7 eligible_candidates=7` : sept documents fictifs acceptés indexés.
- `D4 LOCAL VERIFIED` : réponse factuelle sourcée sur `DM-2026-001` (120 EUR), abstention pour `ZXZ-9999` absent, refus d'une injection de consignes, avec les **vrais modèles locaux**.
- `D3 SQL VERIFIED` : 15 factures fictives, 7 documents acceptés et 2 rejetés, **1 344,00 EUR TTC** conservés après indexation.
- Fin du script : **`D4 LOCAL OK`**. Le RAG reste local ; aucun service IA public ou payant n'a été créé.

**Limites de la preuve :** validation du scénario connu et des cas négatifs testés ; pas de mesure exhaustive de qualité sur des documents arbitraires. Les checks de sécurité réduisent les risques, mais ne garantissent pas l'absence de toute injection ou hallucination. Contrôle Render post-fusion à effectuer séparément.
