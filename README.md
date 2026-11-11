# DocuMind — Intelligence documentaire locale

**DOC 01 · React / TypeScript · Django REST · PostgreSQL · Pandas / Airflow · Metabase · Ollama / ChromaDB / LangGraph**

DocuMind aide à **importer, contrôler, analyser et interroger des documents d'entreprise** sans perdre leur provenance. Il s'adresse à une personne qui reçoit régulièrement des factures, tableaux ou fichiers PDF et veut en extraire des informations vérifiables.

L'application complète fonctionne **localement**. Le seul service distant historique est une **démonstration backend D1 en lecture seule** sur Render, qui n'héberge ni la plateforme Full Stack, ni les calculs avancés, ni l'assistant IA.

## 1. À quoi sert DocuMind ?

Imaginez une entreprise qui reçoit des factures PDF, des tableaux CSV et des fichiers Excel :

- retrouver une information nécessite d'ouvrir les fichiers un à un ;
- les montants et les fournisseurs sont difficiles à réconcilier ;
- certaines pièces peuvent comporter des incohérences ;
- un chiffre doit toujours pouvoir être relié à sa source ;
- une question posée à l'IA ne doit pas produire une réponse financière sans preuve.

**DocuMind transforme les fichiers en informations structurées, contrôlées, exploitables et traçables.**

```text
Importer → Contrôler (D2) → Analyser (D3)
                   ↓
             Document accepté → Indexer (D4) → Interroger l'IA
                   ↓
              Historique / provenance
```

**Attention :** importer un fichier ne revient pas à accepter une facture. Le contrôle D2, l'indexation et la génération de réponse IA sont des opérations distinctes. Les documents rejetés sont exclus des montants financiers validés.

## 2. Découvrir les cinq pages

| Espace | Ce que vous y faites |
| --- | --- |
| **Vue d'ensemble** | Consultez le nombre de documents, les acceptations/rejets, les montants vérifiés et les derniers documents. |
| **Documents** | Importez un PDF textuel, CSV ou XLSX (5 Mio maximum), filtrez le catalogue, ouvrez une fiche, contrôlez les données et consultez les anomalies, extraits et traitements. |
| **Analyse & KPI** | Analysez les dépenses dans le temps et par fournisseur, la qualité des documents, la réconciliation par devise et les anomalies, depuis les vues SQL vérifiées. |
| **Assistant IA** | Interrogez les documents acceptés et indexés. Le moteur local recherche des passages, produit une réponse accompagnée de citations ou s'abstient lorsque la preuve manque. |
| **Historique** | Recherchez les opérations réellement enregistrées, leurs dates, leurs acteurs et les documents concernés. |

L'interface présente ces cinq espaces sous forme de cockpits sombres, bleu marine et vert menthe, à panneaux transparents. Les mises en page s'adaptent à la place réellement disponible : fenêtre classique, grand écran ou mobile.

### « Découvrir DocuMind » : apprendre à s'en servir

Accessible depuis la barre supérieure de l'application (et depuis l'Assistant IA), le guide comprend :

1. **Je débute** : parcours commençant par l'import d'un document, avant la lecture des indicateurs.
2. **Explorer les cinq pages** : quinze consignes courtes avec l'action à effectuer et son résultat attendu.
3. **Voir dans l'application** : mise en évidence du véritable bouton ou module concerné, sans cliquer ni déclencher de traitement à votre place.

Le guide indique aussi lorsqu'une fonction n'est pas disponible dans une démo en lecture seule ou sans rôle opérateur. Il peut être fermé à tout moment.

### Exemple concret — facture fictive

Une entreprise importe une facture fictive de 120 €. Le document apparaît dans le catalogue. **Après** lancement du traitement D2, ses montants sont contrôlés. S'il est accepté, les informations validées peuvent entrer dans les KPI SQL ; ses passages peuvent ensuite être indexés pour l'IA. Les opérations sont retrouvables dans l'Historique. En cas de rejet, le montant n'entre pas dans les totaux validés et le document ne peut pas être indexé.

Cet exemple explique le parcours ; il n'est **pas** une transaction automatiquement effectuée à l'ouverture de l'application.

## 3. Architecture technique

| Brique | Technologie et responsabilité |
| --- | --- |
| Interface | React 19, TypeScript strict, Vite, CSS responsive, tests Vitest / Playwright |
| API / sécurité | Django REST Framework, sessions Django, CSRF, autorisations opérateur |
| Stockage | PostgreSQL local : documents, traitements, factures, anomalies, audit |
| Traitement D2 | Python, Pandas, openpyxl, pypdf ; normalisation, validations, provenance et rejeu idempotent |
| Orchestration | Apache Airflow (profil Docker facultatif `pipeline`) |
| Analyse D3 | Vues SQL gouvernées `bi`, rôle lecteur restreint et Metabase local (profil `analytics`) |
| Assistant D4 | Ollama (`qwen2.5:1.5b`, `nomic-embed-text`), ChromaDB, LangGraph, citations vérifiées et abstention |

Les chiffres financiers sont calculés depuis les données validées, **pas par un modèle génératif**. Les sources restent consultables ; les devises ne sont pas additionnées implicitement.

## 4. Récupérer le projet

### Prérequis

- Windows avec **PowerShell** et **Docker Desktop** démarré en mode conteneurs Linux (ou environnement capable d'exécuter Docker Compose) ;
- **Git** pour récupérer les sources ;
- une connexion Internet lors de la première récupération des images Docker et des modèles Ollama ;
- suffisamment de mémoire et d'espace disque pour les conteneurs. Metabase et Airflow peuvent rester arrêtés pendant l'utilisation quotidienne de l'interface et de l'IA.

Depuis PowerShell :

```powershell
git clone https://github.com/sogoyou8/DocuMind.git
cd DocuMind
docker compose config --quiet
```

Si vous disposez déjà d'une copie locale du dépôt, ne reclonez pas : mettez-la à jour après avoir vérifié vos modifications non enregistrées avec `git status`, puis utilisez `git pull --ff-only` sur la branche souhaitée.

### Lancement recommandé : installation et recette complète

```powershell
.\scripts\verify-d51.ps1
```

Ce script appelle la recette D5, démarre les conteneurs requis, prépare les données de test fictives, contrôle Django, la cohérence SQL, les modèles IA locaux, TypeScript/Vite/Vitest et les parcours Chromium Playwright. Il **préserve les volumes Docker** et n'effectue aucun déploiement public. Les tests réels peuvent nécessiter le téléchargement préalable des images et modèles.

Une fois les services prêts, ouvrez **http://127.0.0.1:5173**.

### Se connecter

- **Identifiant local :** `documind-local`
- **Mot de passe :** créé aléatoirement et conservé sur votre machine dans `data/local/d5-operator.json`, fichier ignoré par Git.

Pour copier uniquement le mot de passe dans le presse-papiers Windows :

```powershell
$account = Get-Content "data/local/d5-operator.json" -Raw | ConvertFrom-Json
$account.password | Set-Clipboard
```

Ne publiez jamais ce fichier et n'intégrez pas le mot de passe dans une capture, un commit ou un rapport. Le mot de passe n'est pas inclus dans le dépôt.

### Redémarrer après installation

```powershell
docker compose --profile ai --profile ui up -d postgres api ollama rag web
```

- Interface : **http://127.0.0.1:5173**
- API locale : **http://127.0.0.1:8001/api/v1/health/**
- API Django de base : **http://127.0.0.1:8000/api/v1/health/**

Pour les modules facultatifs :

```powershell
docker compose --profile analytics up -d metabase
docker compose --profile pipeline up -d airflow
```

Metabase : **http://127.0.0.1:3033** ; Airflow : **http://127.0.0.1:8088**. Leur initialisation et provisionnement complets sont pris en charge par les scripts `verify-d3.ps1` et `verify-d2.ps1`.

Pour arrêter les services sans effacer les données :

```powershell
docker compose --profile ai --profile ui stop web rag ollama
```

**N'exécutez pas `docker compose down -v`** si vous souhaitez conserver vos bases, documents, modèles et index locaux.

## 5. Utiliser DocuMind pas à pas

1. **Documents → Choisir un fichier** : sélectionner un PDF textuel, CSV ou XLSX, puis cliquer sur **Importer**.
2. **Documents → Catalogue** : retrouver le fichier et ouvrir sa fiche. Pour un document reçu et si votre session le permet, lancer **Traiter avec D2** ; examiner les factures et anomalies.
3. **Vue d'ensemble / Analyse & KPI** : consulter uniquement les données financières issues des traitements acceptés. Vérifier les unités, devises et exclusions.
4. **Documents → fiche validée** : si le moteur local est disponible, lancer **Indexer pour l'IA**. Les documents rejetés ne sont pas admissibles à l'index.
5. **Assistant IA** : saisir une question, l'envoyer et contrôler les citations vers les extraits sources. Une réponse peut être refusée si les preuves manquent.
6. **Historique** : filtrer les événements et ouvrir le document lié.

Le guide intégré **« Découvrir DocuMind »** accompagne ces actions visuellement, une étape à la fois, sans les exécuter automatiquement.

## 6. Vérifier et tester

La recette complète reste :

```powershell
.\scripts\verify-d51.ps1
```

Pour des contrôles ciblés après une modification du frontend :

```powershell
docker compose --profile ui exec -T web npm run typecheck
docker compose --profile ui exec -T web npm run build
docker compose --profile ui exec -T web npm test
```

Pour l'intégration backend et IA : `docker compose --profile ai exec -T rag python manage.py test documents -v 2`. La recette D5.1 comprend en plus les tests Chromium et les données SQL/RAG locales.

**Historique des preuves :** le 10 novembre 2026, avant la refonte premium, la recette D5.1 a passé 58 tests Django, 13 tests Vitest et les scénarios Playwright alors présents, avec vérifications SQL D3 et RAG D4. Le 11 novembre, les cinq pages premium et le guide ont été revus visuellement. **Les nouveaux tests introduits par ces refontes doivent être rejoués : l'examen visuel ne remplace pas une recette automatisée sur le dernier commit.**

Captures et rapports locaux : `frontend/test-results/` et `frontend/playwright-report/`.

## 7. Confidentialité et limites

- **Application Full Stack : locale uniquement.** PostgreSQL, les fichiers importés, Ollama, ChromaDB, Metabase et Airflow ne sont pas déployés pour un accès public.
- **Render Free :** [ancienne API D1 en lecture seule](https://documind-d1-api-htpg.onrender.com), uniquement des métadonnées synthétiques ; pas de calcul D3 ni d'assistant D4. Disponibilité et persistance non garanties.
- Les documents rejetés ne contribuent pas aux montants validés ni à l'index IA.
- La recherche du catalogue s'applique à la page actuellement chargée ; l'Historique n'est pas une recherche globale sur l'intégralité de la base.
- Les modèles IA peuvent se tromper : **une citation est une aide à la vérification, pas une garantie de justesse**.
- Les exemples et factures du corpus sont fictifs. Ne pas importer de pièces privées dans un service tiers.
- Les ports Compose sont limités à l'interface locale `127.0.0.1`.

## 8. Structure du dépôt

```text
backend/       API Django, PostgreSQL, traitements D2-D5, RAG local
frontend/      React/TypeScript, cinq pages, découverte guidée, tests
airflow/       DAG et exécution du pipeline
scripts/       Recettes locales, scripts SQL/Metabase, vérifications
docs/          Énoncé, architecture, UML, états D0-D5, preuves
data/local/    Secrets et données locales (ignorés par Git)
compose.yaml   Services Docker et profils facultatifs
render.yaml    Contrat de la démo historique backend D1 uniquement
```

## 9. Documentation et présentation

- [Sujet du projet — PDF](docs/Sujet-du-projet.pdf) et [version Markdown](docs/Sujet-du-projet.md).
- [Architecture technique](docs/ARCHITECTURE.md), [diagrammes UML](docs/UML.md) et [feuille de route](docs/ROADMAP.md).
- [Recette V1 D5](docs/ETAT-D5.md), [plan de finition D5.1](docs/PLAN-D51.md).
- **Abyss Showcase** : la fiche DocuMind présente l'interface et sa documentation ; elle ne doit **pas** prétendre proposer une démo publique de l'application Full Stack locale.

---

DocuMind privilégie la **reproductibilité, la provenance des données et l'absence de résultats inventés**. Un lecteur doit pouvoir identifier la source d'un document, comprendre sa validation et reproduire les démonstrations dans son environnement local.
