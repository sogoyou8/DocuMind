# DocuMind

**DOC 01 — Plateforme d'intelligence documentaire | D1-D5 validés fonctionnellement en local · Render Free en lecture seule**

DocuMind est un projet d'apprentissage professionnel **en cours de développement**. Son ambition est de traiter des documents d'entreprise fictifs (PDF textuels, CSV et XLSX), de structurer les informations dans PostgreSQL, d'orchestrer les traitements avec Airflow et d'offrir une analyse BI et un assistant documentaire IA local.

> **État réel :** D0 documenté et D1 fusionné dans `main` après recette locale du 9 novembre 2026 : 11 tests Django réussis sur PostgreSQL, migrations cohérentes, contrôles OpenAPI stricts et healthcheck OK. Déploiement Render gratuit **Live** le 9 novembre 2026 : migrations et initialisation de 3 exemples synthétiques réussies, service Gunicorn en ligne et healthcheck HTTP 200. L'API reste en lecture seule sur Render ; pas de base PostgreSQL hébergée ni de frais engagés. **D2 valide localement le 9 novembre 2026 : 30/30 tests reussis sur PostgreSQL, 3 factures fictives acceptees / 1 document rejete, 240 EUR TTC, rejeu sans doublons et execution du DAG Airflow reussie.** **D3 validé localement le 9 novembre 2026 : 36/36 tests réussis, 9 vues BI, 15 factures fictives acceptées pour 1 344 EUR TTC, lecteur SQL strictement en lecture seule, Metabase initialisé avec 12 vraies questions et leurs contrôles de cohérence réussis.** **D4 validé localement le 9 novembre 2026 : 47/47 tests dans le conteneur IA, 7 documents indexés, réponse 120 € sourcée, abstention et refus d'injection, 1 344 € TTC de D3 préservés.**

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

Une **prévisualisation publique du socle backend D1** existe sur Render, mais aucune démonstration de l'application Full Stack complète à ce stade. Le lien de code renvoie au présent dépôt et la fiche Abyss Showcase montre toujours les **intentions et l'architecture D0**. Le backend D1 et le pipeline D2 sont valides localement. La demo Render Free reste volontairement limitee aux metadonnees fictives et a la lecture seule. D3 est validé localement avec le tableau de bord Metabase ; D4-D5 restent à développer.

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

## D2 — Traitement documentaire deterministe (recette locale reussie)

Le pipeline D2 utilise **Pandas, openpyxl et pypdf** en local. Il extrait les tables CSV/XLSX ou les pages d'un PDF textuel, normalise les champs requis des factures (fournisseur, numéro, date, devise, HT, TVA, TTC), conserve la provenance et les anomalies, puis produit uniquement les factures acceptées. Les documents incohérents sont mis en quarantaine sans contribuer aux indicateurs. La reprise est idempotente par document/version.

- Commandes : `python manage.py seed_d2 --process`, `process_pending`, `verify_d2`.
- API locale : `POST /api/v1/documents/{id}/process/`, `GET /api/v1/invoices/`, `/processing-runs/`, `/records/`, `/quality-issues/`.
- Airflow local facultatif au quotidien, **obligatoire à la recette D2 complète**, via `docker compose --profile pipeline up -d airflow`. Interface Airflow sur http://127.0.0.1:8088.
- Recette complète PowerShell : `.\scripts\verify-d2.ps1`, en conservant les volumes PostgreSQL. Le script inclut les tests existants et une exécution du vrai DAG Airflow.
- Corpus entièrement fictif et reproductible : 3 factures acceptées, 1 document rejeté ; montant validé attendu 240,00 EUR TTC (aucun montant inventé).
- Documentation : [État et recette D2](docs/ETAT-D2.md).

**Recette du 9 novembre 2026 :** `Ran 30 tests ... OK`, `D2 LOCAL VERIFIED` et `D2 LOCAL OK`, avec DAG Airflow termine en etat `success`. La tache Airflow n'a pas traite de nouveau document, puisque la file de traitement etait deja vide. Le service public Render Free reste une demo D1 en lecture seule, sans Airflow heberge.

## D3 — SQL analytique et Metabase local (recette validée)

Les indicateurs D3 proviennent exclusivement des tables de factures déjà **acceptées et validées** dans PostgreSQL. Le schéma gouverné `bi` fournit neuf vues : factures, qualité documentaire, anomalies, dépenses mensuelles, fournisseurs, formats, devises et états. Un rôle SQL indépendant `documind_bi` n'a droit qu'à lire ces vues ; pas d'accès aux fichiers bruts ou aux tables privées.

Le profil local `analytics` lance **Metabase Open Source v0.64.1** sur [http://127.0.0.1:3033](http://127.0.0.1:3033), avec une configuration persistante dans un volume Docker. Le script de provisionnement API crée **12 questions SQL réelles** dans un tableau de bord à deux onglets : Synthèse (KPI, courbe mensuelle, dépenses fournisseurs, anomalies) et Traçabilité (factures, documents, sources, totaux par devise).

Le corpus fictif étend D2 à cinq mois : **15 factures acceptées pour 1 344,00 EUR TTC**, **7 documents acceptés et 2 rejetés**. Ce sont des valeurs *fictives* issues des fichiers synthétiques versionnés et vérifiées dans PostgreSQL puis Metabase par la recette du 9 novembre 2026. Les montants de devises différentes ne sont jamais additionnés.

**Recette complète vérifiée sous Windows / Docker Desktop :**

```powershell
.\scripts\verify-d3.ps1
```

Le script vérifie les régressions D1/D2, les KPI SQL, les permissions effectives du lecteur, puis installe et exécute le tableau de bord Metabase et ses requêtes. Les mots de passe sont générés dans `data/local/d3-metabase-secrets.json`, ignoré par Git ; ne pas les partager. La démo publique Render reste **D1 en lecture seule**, sans Metabase hébergé et sans abonnement.

- [Contrat, preuves et recette D3](docs/ETAT-D3.md)
- Migration PostgreSQL : `backend/documents/migrations/0003_bi_views.py` ; SQL : `backend/documents/bi/views_v1.sql`
- Configuration Metabase : `scripts/provision_metabase.py` ; recette : `scripts/verify-d3.ps1`

**Statut : D3 validé localement**. La recette du 9 novembre 2026 s'achève par `D3 LOCAL OK` après `Ran 36 tests ... OK`, `D3 SQL VERIFIED`, `D3 SQL ROLE VERIFIED` et `D3 METABASE OK`. Le tableau de bord contient 12 questions réellement exécutées ; ses valeurs, devises, anomalies et totaux sont réconciliés. **Limite :** aucune capture ou inspection UX du rendu Metabase n'est encore jointe à cette validation, et aucun Metabase public n'est hébergé.

## D4 — Assistant documentaire IA local (recette validée)

Le service optionnel `rag` ajoute une API documentaire locale sur **http://127.0.0.1:8001**, avec ChromaDB (stockage privé persistant), `nomic-embed-text` (embeddings via Ollama), `qwen2.5:1.5b` (génération locale) et LangGraph (recherche, réponse, contrôle et abstention).

L'index repose **uniquement sur les documents acceptés par D2** ; `ChunkReference` conserve les identifiants du document, du traitement, de la page/ligne et l'empreinte SHA-256 de chaque passage. Une citation ne peut être affichée que si PostgreSQL confirme qu'elle correspond encore à une source autorisée. Les instructions contenues dans un document ne deviennent jamais des commandes système. Le filtrage des injections réduit le risque mais ne garantit pas l'absence totale de réponses trompeuses : une citation doit toujours pouvoir être vérifiée.

- `POST /api/v1/documents/{uuid}/index/` : index local réservé opérateur/admin.
- `POST /api/v1/assistant/ask/` : réponse `answered` avec sources, ou `abstained` sans citation inventée.
- `GET /api/v1/assistant/status/` : état de configuration du service local authentifié.
- `python manage.py index_pending --limit 20` et `verify_d4` : commandes d'indexation et de vérification.
- Recette PowerShell complète : `.\scripts\verify-d4.ps1` (lance et teste Ollama et Chroma en local, sans service payant).
- Voir [État, sécurité et validation D4](docs/ETAT-D4.md).

**État : D4 validé par `D4 LOCAL OK` après 47 tests réussis dans le service IA et vérification réelle de la réponse sourcée, de l'abstention, de l'injection testée et des KPI D3.** La qualité du LLM n'est pas garantie pour toutes les questions. Le backend Render Free reste limité à la démo D1 en lecture seule, sans Ollama ni index public. L'interface React et la release V1.0 restent prévues en D5.

## D5 — Frontend React / TypeScript V1.0 (recette fonctionnelle validée)

Le dossier `frontend/` contient le cockpit responsive React + Vite, avec cinq espaces opérationnels :

- **Vue d'ensemble** : documents/états, résultats SQL D3 en EUR lorsqu'ils existent, évolution mensuelle, fournisseurs et vérification des sources.
- **Documents** : catalogue, recherche/filtres sur la page, pagination, import local authentifié, traitement D2, indexation D4 et fiche détaillée (factures, extraits, anomalies, journal).
- **Analyse & KPI** : données réelles de PostgreSQL `bi` par devise, montants acceptés, fournisseurs et anomalies. Aucun chiffre financier fictif sur Render.
- **Assistant IA** : questions localement routées vers Ollama/ChromaDB/LangGraph, citation cliquable du document et de la ligne, abstention en absence de preuve. Désactivé dans la démo publique.
- **Historique** : événements SQL réels, horodatage et navigation vers le document concerné.

Le backend D5 ajoute une **session Django avec CSRF**, un compte opérateur local privé, ainsi que `GET /api/v1/analytics/` et `GET /api/v1/audit/` ; les autres API D1-D4 restent inchangées. Le mode public en lecture seule protège toujours les fichiers et n'invente ni dépenses ni réponses IA.

La recette complète sous Windows et Docker Desktop est :

```powershell
.\scripts\verify-d5.ps1
```

Ce script démarre les services gratuits locaux, vérifie Django et les calculs D3/D4, installe la V1 frontend, exécute TypeScript, Vite, Vitest, Chromium Playwright (démo, mobile, parcours connecté avec citation), puis valide de nouveau les KPI. Les secrets locaux sont stockés sous `data/local/d5-operator.json` (ignoré par Git) ; l'application se consulte sur **http://127.0.0.1:5173** avec `documind-local` une fois le script passé.

[Spécifications D5, preuves attendues et limites](docs/ETAT-D5.md)

**Validation observée le 10 novembre 2026 : `D5 LOCAL OK`.** Le conteneur IA/PostgreSQL a réussi 58 tests Django (aucun saut) ; Django/OpenAPI et D3/D4 ont été vérifiés avec les vrais modèles ; TypeScript, build Vite et Vitest ont réussi ; les 3 tests Chromium Playwright ont validé démo bureau, navigation mobile sans débordement horizontal et parcours local connecté, KPI SQL, citation IA. **L'examen visuel des captures et le gel/tag V1.0 restent distincts** : aucun déploiement du frontend Vercel n'est annoncé ; Render Free n'héberge pas l'IA.

## D5.1 — Finition UX/UI transversale (branche isolée)

La revue visuelle des cinq écrans et de la fiche documentaire du 10 novembre 2026 a été convertie en [plan de corrections mesurables](docs/PLAN-D51.md). Le chantier corrige les débordements, compresse les cockpits sur les résolutions bureau observées, conserve les filtres et onglets durant les défilements, harmonise les événements et données extraites en français, et explicite les anomalies de validation à partir des données réelles.

L'assistant sait maintenant répondre **sans appel IA ni fausse citation** aux questions générales sur les capacités et formats de DocuMind ; toute question documentaire reste soumise au RAG D4, aux citations vérifiables et à l'abstention. Une réponse EUR TTC numérique citée est formatée uniquement lorsque son contexte le justifie.

Cette finition se valide par :

```powershell
.\scripts\verify-d51.ps1
```

La commande exécute intégralement D5 puis les nouveaux tests Vitest et Playwright (1920×993, 1649×928, 1440×900, 390×844). Elle produit `D5.1 LOCAL OK` **uniquement après les tests locaux réussis**. Les captures se retrouvent dans `frontend/test-results/`.

**Statut D5.1 au 10 novembre 2026 : `D5.1 LOCAL OK` observé.** Recette Windows/Docker complète réussie : 58/58 tests Django, typecheck/build Vite, 13/13 Vitest, SQL D3 réconcilié, vrai RAG D4, et 4/4 scénarios Playwright Chromium (dont les cinq vues à quatre résolutions). **Revue esthétique des nouvelles captures encore nécessaire avant fusion et gel V1.0.** Aucun changement de service public ou de moteur D1–D4.

### Revue visuelle finale — complément D5.1

Les vingt captures manuelles confirment la cohérence du rendu et de la traçabilité, mais ont révélé des défilements externes sur certains bureaux et une formulation d'aide non reconnue (`En quoi consiste cette app ?`). Deux correctifs ciblés et des assertions Playwright supplémentaires sont ajoutés sur la branche D5.1 : mode compact pour les fenêtres CSS de 1200 px de large et 730 px de haut au minimum, défilements internes, réponses de présentation de l'application sans appel au RAG. **Nouvelle recette exécutée et réussie sur les derniers correctifs le 10 novembre 2026 : 58/58 Django, 13/13 Vitest, 4/4 Playwright, dont les contrôles de débordement horizontal et vertical à 1320×742 CSS.** La revue esthétique des captures produites après ce correctif reste distincte, avant fusion.

### D5.1 — Finition des captures 1320×742

Dernière revue : les cinq vues tiennent dans la fenêtre compacte, mais la notification de connexion restait affichée par-dessus les panneaux et la ligne sous le champ de l'assistant était légèrement tronquée. La notification de succès se ferme désormais automatiquement après 4,5 s (les erreurs restent lisibles jusqu'à fermeture) ; la hauteur de l'assistant est ajustée aux fenêtres de bureau courtes. Un test Playwright vérifie le composeur intégralement visible et des captures non masquées par une notification. **Nouveaux correctifs en attente de recette locale et de contrôle final avant fusion de la PR #7.**
