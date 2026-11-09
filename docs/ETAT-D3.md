# DocuMind D3 — SQL métier, indicateurs fiables et Metabase local

## Mission

D3 transforme les **factures réellement acceptées par D2** en indicateurs BI vérifiables, sans modifier les données sources, sans inventer de montants et sans hébergement payant. Les données de démonstration sont **entièrement fictives**.

### Livrables

1. **Schéma SQL `bi` isolé** créé en migration `0003_bi_views.py` sur PostgreSQL uniquement. Sur SQLite/Render Free, la migration n'exécute aucune création SQL, et la démo publique demeure limitée aux trois fiches D1 en lecture seule.
2. **Neuf vues SQL gouvernées** dans `documents/bi/views_v1.sql` : `validated_invoices` (une ligne/facture), `document_quality` (une ligne/document), `quality_issues` (une ligne/anomalie), `spending_monthly`, `spending_suppliers`, `spending_formats`, `currency_totals`, `document_status_counts` et `issue_code_counts`.
3. **Compte PostgreSQL `documind_bi`** : accès SELECT aux vues `bi` exclusivement ; pas de lecture des tables brutes (fichiers, utilisateurs, enregistrements), pas d'INSERT/UPDATE/DELETE, ni de superutilisateur. Le mot de passe est généré et sauvegardé uniquement sur le PC, jamais commité.
4. **Metabase Open Source local**, profil Docker `analytics`, image épinglée `metabase/metabase:v0.64.1`. Son H2 de configuration est persistant via volume Docker **uniquement pour démonstration locale**, non pour production. Port `127.0.0.1:3033`.
5. **Tableau de bord et questions réels**, provisionnés via l'API Metabase gratuite, sans fonctionnalités Pro : deux onglets `Synthese` et `Tracabilite`, 12 questions sauvegardées (KPI, graphiques, preuves et tableaux). Le script est réexécutable sans recréer des copies de chaque élément.
6. **Jeu fictif enrichi** : `seed_d3 --process` conserve les 4 fichiers D2 (3 acceptés + 1 rejeté) et ajoute 5 fichiers D3 (4 CSV multi-lignes acceptés + 1 CSV invalide).
7. **Recette SQL indépendante** : `verify_d3` compare les vues à l'ORM `Invoice`, au corpus de fichiers et aux agrégations selon la devise. `verify_bi_reader` prouve les permissions effectives de la connexion SQL Metabase. Le provisionnement vérifie que les graphiques mois/fournisseurs/devise, les comptes de documents et les tables de détail sont concordants.

## Définitions des indicateurs

| Indicateur | Numérateur / grain | Restriction et source |
|---|---|---|
| Factures acceptées | `COUNT(*)` dans `bi.validated_invoices` | Une facture par ligne ; document `ACCEPTED` ou `INDEXED`, run `SUCCEEDED`, source `UPLOAD` |
| Montant TTC EUR | `SUM(total)` | Factures acceptées avec `currency='EUR'` uniquement ; jamais de conversion implicite |
| Dépense mensuelle | Somme TTC par `date_trunc('month', issued_on)` et devise | Date **de facture**, pas date d'import ; regroupement séparé par devise |
| Dépense fournisseur | Somme TTC par fournisseur et devise | Même population de factures validées |
| Documents rejetés | `COUNT(*)` dans `bi.document_quality` | Documents sources `UPLOAD`, un seul rang par document |
| Taux de rejet (%) | Documents `REJECTED` / tous documents `UPLOAD` × 100 | Comprend les documents en attente dans le dénominateur ; non égal au taux de factures rejetées |
| Anomalies par règle | Compte de `bi.quality_issues` | Les anomalies sont attachées à la dernière exécution du document |
| Détails vérifiables | Document, localisateur, fournisseur, date, HT, TVA, TTC | Aucune URL de téléchargement privé, aucun champ `raw_fields` ni fichier brut exposé à Metabase |

Un document rejeté peut conserver ses lignes et anomalies en PostgreSQL, mais ne contribue **jamais** aux sommes. Les montants de devises différentes sont **séparés**.

## Corpus reproductible (simulation uniquement)

| Période de facture | Factures validées | TTC EUR |
|---|---:|---:|
| Juillet 2026 | 3 | 240,00 |
| Août 2026 | 3 | 270,00 |
| Septembre 2026 | 3 | 306,00 |
| Octobre 2026 | 3 | 288,00 |
| Novembre 2026 (D2) | 3 | 240,00 |
| **Total fictif** | **15** | **1 344,00** |

Par fournisseur fictif : Atelier Fictif **588 €**, Librairie Fictive **486 €**, Imprimerie Fictive **270 €**. Au total : **9 documents**, dont **7 acceptés et 2 rejetés** ; 2 anomalies intentionnelles de type `TOTAL_MISMATCH`.

Ces valeurs sont des **attendus calculés à partir des fixtures versionnées** ; tant que la recette locale n'est pas exécutée avec succès, il ne faut pas les présenter comme des observations Metabase mesurées.

Les vues SQL couvrent tous les documents locaux autorisés : si d'autres documents ont été importés, les totaux globaux peuvent dépasser ceux du seul corpus fictif. La recette compare alors les fixtures par ID et réconcilie les totaux globaux indépendamment avec les factures validées.

## Installation locale et recette complète

Sous Windows 11, depuis le dépôt DocuMind, Docker Desktop démarré et branche D3 sélectionnée :

```powershell
.\scripts\verify-d3.ps1
```

Le script :
- exécute les tests Django D1/D2/D3 sur PostgreSQL, y compris le contrôle des migrations et OpenAPI ;
- crée et rejoue le corpus de manière idempotente puis effectue `verify_d3` ;
- crée des mots de passe aléatoires localement sous `data/local/d3-metabase-secrets.json` (ignoré par Git) ;
- configure et vérifie les droits `documind_bi` ;
- démarre `docker compose --profile analytics up -d metabase` et attend la disponibilité de l'API ;
- initialise l'administrateur local si nécessaire ; crée la connexion SQL, la collection, 12 questions et le tableau de bord avec deux onglets ;
- exécute les 12 questions et réconcilie les KPI avec les tableaux de détail.

L'interface est accessible uniquement sur ton PC : **http://127.0.0.1:3033**. L'e-mail de connexion est `admin@documind.local` ; le mot de passe est dans le fichier privé local. Ne jamais partager ni commiter ce fichier.

Le premier lancement télécharge l'image Metabase et peut consommer davantage de RAM. Après la recette, arrêter la seule BI avec `docker compose --profile analytics stop metabase`. **Ne pas lancer `docker compose down -v`** (cela détruirait les volumes PostgreSQL, Airflow et Metabase).

`-SkipCoreTests` ne remplace pas la recette complète : il permet seulement un relancement ciblé de D3 après la première réussite des tests.

## Critères de sortie D3

- [x] Tous les tests D1/D2/D3 réussissent et aucune migration manquante.
- [x] `verify_d3` confirme le corpus, les sommes et les grains sans double comptage.
- [x] Le rôle `documind_bi` peut lire les vues mais pas les tables d'origine.
- [x] Metabase démarre réellement, avec les 12 questions et les deux onglets.
- [x] Les graphiques et KPI concordent avec les contrôles SQL indépendants.
- [ ] Aucun service payant ni exposition de données brutes : conception locale vérifiée ; contrôle de non-régression Render **à confirmer après la fusion GitHub**.

**Statut final de la recette : validée localement le 9 novembre 2026.** Les quotas GitHub Actions sont épuisés ; les preuves proviennent de PowerShell et Docker Desktop. Les captures visuelles de Metabase et la non-régression Render post-fusion restent des contrôles distincts.

## Hors D3

D4 : ChromaDB, Ollama, LangGraph et réponses sourcées. D5 : interface React, expérience complète, QA et V1.0. Le tableau de bord Metabase n'est pas l'interface utilisateur finale.

## Preuves observées — recette locale du 9 novembre 2026

Le journal transmis depuis le PC confirme, dans cet ordre :

- `Applying documents.0003_bi_views... OK`, `No changes detected` et `Ran 36 tests in 5.345s` puis `OK` (tests D1+D2+D3 et migrations PostgreSQL, OpenAPI et santé inclus).
- Deux passages de `seed_d3 --process` : quatre CSV mensuels acceptés, un fichier avec erreur rejeté ; au second passage, `skipped=True` sans doublons.
- `D3 SQL VERIFIED` : 15 factures fictives acceptées, 7 documents acceptés, 2 rejetés, 1 344,00 EUR TTC, 5 périodes, fournisseurs/devises/anomalies réconciliés.
- `D3 SQL ROLE VERIFIED` : compte `documind_bi` autorisé uniquement en lecture des vues BI, sans accès SQL aux tables métier brutes.
- Metabase `v0.64.1` démarré et `Metabase API health OK` ; administrateur local authentifié, base BI connectée, **12 questions SQL créées et réellement exécutées**, tableau de bord `/dashboard/1` sauvegardé avec deux onglets.
- `D3 METABASE OK` : `accepted_invoices=15`, `EUR_TTC=1344.0`, `rejected_documents=2`, `quality_issues=2` ; sommes mensuelles, fournisseurs et devises recoupées.
- Ligne finale : **`D3 LOCAL OK: SQL views, fiscal metrics, read-only account and Metabase dashboard`**.

**Limites de portée :** toutes ces valeurs concernent un corpus fictif et ne décrivent aucune entreprise réelle. Le journal confirme les API, les cartes et les calculs, **pas la disposition visuelle sur écran**. Airflow n'a pas été relancé lors de cette recette (option `-SkipAirflow`) : sa validation propre est déjà documentée au jalon D2. Metabase fonctionne uniquement en local à `127.0.0.1:3033`. Le service Render Free doit rester une démonstration D1 en lecture seule après fusion.
