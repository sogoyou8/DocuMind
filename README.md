# DocuMind — Intelligence documentaire locale

**DOC 01 · React / TypeScript · Django REST · PostgreSQL · Pandas / Airflow · Metabase · Ollama / ChromaDB / LangGraph**

DocuMind aide à **importer, contrôler, analyser et interroger des documents d'entreprise** sans perdre leur provenance. Il s'adresse à une personne qui reçoit régulièrement des factures, tableaux ou fichiers PDF et veut en extraire des informations vérifiables.

L'application complète fonctionne **localement**. Le service Render historique présente désormais une **démonstration interactive simulée de la V1.0** avec un corpus fictif et des réponses préenregistrées ; son API réelle demeure limitée au **backend D1 en lecture seule**. Ni PostgreSQL D3, ni Airflow, ni ChromaDB/Ollama ne sont exécutés sur Render.

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

**Affichage mono-écran (12 novembre 2026) :** sur les écrans de bureau (largeur supérieure à 1080 px et hauteur d’au moins 700 px), les cinq pages occupent exactement la hauteur disponible dans le navigateur. Les graphiques, les indicateurs et les modules principaux restent visibles ensemble ; seuls les catalogues, les inspecteurs, la conversation et les événements trop longs défilent dans leur zone. En dessous de ces dimensions, une mise en page défilante et responsive est conservée pour éviter la perte de contenu. Le mode démo reste une simulation sans backend D2/D3/D4 public.

### Alignement visuel PxM de la démonstration publique (13 novembre 2026)

La présentation Render reprend les mêmes principes visuels que le cockpit premium local : palette noir/marine/menthe, typographies DM Sans/Manrope, logo empreinte, pictogrammes, illustrations translucides, bordures et ombres glassmorphism. Le bandeau des vues **Vue d’ensemble**, **Documents** et **Analyse & KPI** regroupe désormais le titre, le décor et les quatre KPI, au lieu d’une rangée indépendante. Les panneaux conservant davantage de contenu utilisent un défilement interne pour respecter la composition mono-écran sur ordinateur.

Le rapprochement est **visuel et fonctionnel côté navigateur**, et non une duplication du frontend React. La bannière « Mode démonstration » et la mention du backend D1 restent volontairement visibles ; aucune capacité backend locale n'est rendue publique. Contrôles statiques : code JavaScript compilable, rendu des cinq vues en DOM simulé, quatre KPI inclus dans les bandeaux premium, filtres et inspector Documents, et exemple d'assistant à réponse préenregistrée. Le contrôle pixel-par-pixel dans un véritable navigateur reste une validation visuelle distincte.

### Démonstration interactive publique — Render

**Adresse :** https://documind-d1-api-htpg.onrender.com

La page d’accueil du service Render D1 présente les cinq écrans (Vue d’ensemble, Documents, Analyse & KPI, Assistant IA, Historique) avec les données fictives de référence. Les documents, les graphiques et les montants sont explicitement identifiés comme un **scénario public statique**. Les filtres, la sélection de documents et les réponses préenregistrées constituent de vraies interactions navigateur, mais **ne déclenchent ni extraction, ni SQL D3, ni RAG Ollama/ChromaDB**.

Le lien « État API D1 » conserve l’accès au véritable endpoint de santé de la démo. Les routes API d’écriture sont interdites en mode `DOCUMIND_DEMO_READONLY=1`. L'application locale reste la référence pour la démonstration technique Full Stack et les véritables citations produites par le modèle.

**Contrôles :** les cinq vues et interactions ont été testées dans Chromium, dont les recherches/filtres, les réponses sourcées de démonstration, l’abstention et le rendu mobile, sans erreur JavaScript ; les tests Django de non-régression spécifiques à la page ont été ajoutés, mais nécessitent une exécution avec les dépendances Python du projet.

## 7. Confidentialité et limites

- **Application Full Stack : locale uniquement.** PostgreSQL, les fichiers importés, Ollama, ChromaDB, Metabase et Airflow ne sont pas déployés pour un accès public.
- **Render Free :** [présentation interactive simulée](https://documind-d1-api-htpg.onrender.com) des cinq vues de DocuMind sur des exemples fictifs. Recherche, filtres, fiche documentaire et assistant à réponses préenregistrées sont uniquement des interactions côté navigateur. L'API Django du même service reste **D1 en lecture seule**, sans calcul SQL D3 ni assistant D4 réellement exécutés. Disponibilité et persistance non garanties.
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
render.yaml    Service Render existant : présentation HTML simulée + API Django D1 en lecture seule
```

## 9. Documentation et présentation

- [Sujet du projet — PDF](docs/Sujet-du-projet.pdf) et [version Markdown](docs/Sujet-du-projet.md).
- [Architecture technique](docs/ARCHITECTURE.md), [diagrammes UML](docs/UML.md) et [feuille de route](docs/ROADMAP.md).
- [Recette V1 D5](docs/ETAT-D5.md), [plan de finition D5.1](docs/PLAN-D51.md).
- **Abyss Showcase** : le bouton « Voir la démo » doit renvoyer à la **présentation interactive simulée** du service Render, et non à une instance publique de la plateforme Full Stack locale. Les boutons « Code source » et « Document » conservent leurs destinations.

---

DocuMind privilégie la **reproductibilité, la provenance des données et l'absence de résultats inventés**. Un lecteur doit pouvoir identifier la source d'un document, comprendre sa validation et reproduire les démonstrations dans son environnement local.
