# DocuMind — D5 : interface React, QA de bout en bout et préparation V1.0

**État au 10 novembre 2026 : recette fonctionnelle D5 terminée avec `D5 LOCAL OK` sur Windows/Docker Desktop.** Tests Django, API, SQL, assistant IA réel, TypeScript, build Vite, Vitest et Playwright réussis. La revue esthétique manuelle des captures (notamment 1920×993) reste distincte : ne pas présenter cette vérification visuelle comme faite, ni publier l'interface sur Vercel sans vérification.

## Mission et résultat fonctionnel

D5 assemble les composants vérifiés de D1–D4 dans **une application cohérente**. Interface React 19 + TypeScript strict + Vite, design sombre marine/menthe, glassmorphism et bordures à relief, navigation latérale cinq vues, panneaux sur un écran principal et adaptation écran large/tablette/mobile.

| Vue | Fonction réelle | Limite explicitée |
|---|---|---|
| Vue d'ensemble | Documents, états, évolution mensuelle D3 en EUR, principaux fournisseurs et circuit de provenance | La démo Render affiche seulement ses trois métadonnées fictives |
| Documents | Recherche et filtres sur la page, pagination API, import validé côté Django, détails par document : factures, extraits, erreurs, traitements et audit | La recherche et les filtres sont locaux **à la page courante**, pas sur toutes les pages |
| Analyse & KPI | Totaux réellement lus depuis neuf vues gouvernées D3, graphique mensuel EUR, fournisseurs EUR, réconciliation par devise, états, anomalies | Aucun total multidevise ni chiffre inventé ; source SQL indisponible sur Render |
| Assistant IA | Conversation locale vers Ollama/Chroma/LangGraph, réponses sourcées, citations cliquables et abstention explicite | Désactivé dans la démo publique ; le modèle peut se tromper malgré les gardes |
| Historique | Journal horodaté des événements documentaires et accès à la fiche concernée | Les 40 dernières entrées seulement sont chargées ; aucune trace factice publique |

D5 expose également les API **réelles** :

- `GET /api/v1/session/`, `POST /api/v1/session/login/`, `POST /api/v1/session/logout/` : session Django de navigateur avec cookie, CSRF et rôles. La démo refuse toute connexion.
- `GET /api/v1/analytics/` : données D3 PostgreSQL sérialisées en JSON pour l'interface. La démo retourne `available=false` et des tableaux vides.
- `GET /api/v1/audit/?document={uuid}` : traçabilité documentaire authentifiée, sans lien de fichier privé. La démo retourne une liste vide.
- Les API D1/D2/D4 demeurent les autorités pour l'import, le traitement, l'indexation et les questions sourcées. L'interface n'écrit jamais directement dans PostgreSQL.

## Accès et confidentialité

- **Instance locale complète** : `web` Vite sur `http://127.0.0.1:5173`, proxy Django vers `rag:8001` sur le réseau Docker. L'utilisateur `documind-local` est créé en rôle opérateur, sans privilège administrateur, par un script local. Mot de passe fort unique enregistré sous `data/local/d5-operator.json`, ignoré par Git.
- **Prototype de démo publique Vercel** : le dossier `frontend/` contient `vercel.json` pour une éventuelle publication **après validation**. Il redirige uniquement les lectures des API vers Render Free. N'héberge ni Ollama, ni Metabase, ni PostgreSQL ni ChromaDB.
- Les opérations d'écriture sont soumises à la session Django et au jeton CSRF ; le rôle opérateur est nécessaire pour importer, traiter ou indexer.
- La démonstration publique ne doit **jamais** tenter l'import, une transaction ou une réponse IA ; ses états calculés restent indisponibles. Les 3 métadonnées sont identifiées comme fictives.
- Les ports localement publiés sont uniquement sur `127.0.0.1` ; le navigateur et Playwright en Docker sont les seuls consommateurs du proxy Vite. Aucun nom ni mot de passe ne figure dans le dépôt.
- Les pièces privées et les volumes ne sont jamais exposés comme fichiers statiques. La sortie IA indique les extraits de provenance et doit être contrôlée humainement.

## Lancement et recette intégrale

Depuis Windows PowerShell dans le dépôt DocuMind (branche D5, Docker Desktop démarré) :

```powershell
.\scripts\verify-d5.ps1
```

Le script automatique (ASCII compatible PowerShell 5.1) :

1. valide le YAML Compose, démarre PostgreSQL, Django, Ollama/Chroma et la nouvelle interface React, en préservant les volumes existants ;
2. exécute l'audit statique des routes, du CSRF, de l'isolation Docker et du schéma PostgreSQL ;
3. lance tous les tests Django **D1 à D5**, contrôle les migrations et le schéma OpenAPI ;
4. rejoue les fixtures fictives D3 et la vérification D4 avec **vrai** Ollama/Chroma/LangGraph, puis revérifie les 1 344 EUR TTC du corpus ;
5. génère des identifiants privés si nécessaire, installe/réinitialise uniquement le compte opérateur `documind-local` ;
6. attend les healthchecks Django et React puis exécute `npm run typecheck`, `npm run build` et `npm test` ;
7. dans l'image Chromium officielle Playwright, vérifie la démo publique simulée en grand écran et en mobile, puis le **vrai parcours local** : connexion CSRF, lecture des documents et factures, KPI SQL, question IA et citation ;
8. effectue une dernière vérification D3 et écrit **`D5 LOCAL OK`** uniquement si toutes les commandes précédentes ont réussi.

La première installation peut télécharger les images Node/Playwright et les dépendances npm. Les captures sont conservées sous `frontend/test-results/` et `frontend/playwright-report/`, non suivies dans Git.

Pour recopier le mot de passe privé vers le presse-papiers **sur le PC**, sans l'afficher ni le publier :

```powershell
$localAccount = Get-Content "data/local/d5-operator.json" -Raw | ConvertFrom-Json
$localAccount.password | Set-Clipboard
```

Puis ouvrir `http://127.0.0.1:5173`, identifiant `documind-local`. Ne jamais partager le contenu du fichier de secrets.

**Ne jamais exécuter `docker compose down -v`** : les volumes PostgreSQL, Chroma, Ollama, Metabase et Airflow doivent être conservés. Pour arrêter les services V1 sans effacer les données : `docker compose --profile ai --profile ui stop web rag ollama`.

Le raccourci `-SkipBrowser` existe pour les relances ciblées **après** une première validation complète ; il ne remplace pas la preuve E2E V1.

## Critères de validation V1

- [x] 58 tests Django D1–D5 réussis dans le service IA/PostgreSQL, sans test D5 ignoré (`Ran 58 tests ... OK`).
- [x] API Django/OpenAPI/migrations et contrôle CSRF réussis dans la recette.
- [x] Indicateurs D3 cohérents, factures rejetées exclues, 1 344 EUR TTC fictifs préservés (`D3 SQL VERIFIED`).
- [x] Index D4 idempotent, modèle local répond avec citation à `DM-2026-001` (120 EUR) et refuse les références inconnues (`D4 LOCAL VERIFIED`).
- [x] TypeScript strict, build Vite et tests Vitest réussis, tous exigés avant la sortie `D5 LOCAL OK`.
- [x] Playwright Chromium : trois scénarios réussis (`3 passed (18.9s)`), dont démo bureau, mobile sans débordement horizontal et véritable parcours local authentifié avec source IA.
- [ ] Captures : les tests Playwright ont produit des fichiers de capture et vérifié l'absence de débordement horizontal sur mobile ; **l'examen esthétique manuel, notamment à 1920×993, reste à effectuer**.
- [x] Tests backend de confidentialité et refus du mode démo réussis ; contrôle **live Render post-fusion** à enregistrer séparément.
- [ ] Gel visuel et tag V1.0 : réservé à l'issue de l'examen des captures et des vérifications de production ; la fusion du code fonctionnel testé peut être effectuée sans annoncer ce gel.

**Preuve de recette reçue le 10 novembre 2026 :** `D5 STATIC OK`, `System check identified no issues`, `No changes detected`, `Found 58 test(s)`, `Ran 58 tests in 19.078s — OK`, `D3 SQL VERIFIED` (15 factures fictives, 7 documents acceptés, 2 rejetés, 1 344,00 EUR TTC), `D4 LOCAL VERIFIED` (facture 120 EUR sourcée, abstention et injection refusée), healthchecks Django et React (HTTP 200), puis **3/3 scénarios Playwright Chromium réussis** : démo sans KPI inventés, mobile sans débordement horizontal, vrai login/SQL/RAG local avec citation. Le script a terminé sur **`D5 LOCAL OK`** : le build TypeScript/Vite et Vitest, situés avant Playwright, ont donc également réussi. Les fichiers graphiques restent sur l'ordinateur local et n'ont pas été examinés ici. Le mot de passe de l'opérateur reste privé sous `data/local/d5-operator.json`.

## Prochaines décisions après tests

La recette automatique D5 est réussie. Les contrôles finaux distincts sont : vérifier Render Free après fusion, examiner les captures d'écran réelles pour la finition visuelle, puis décider séparément du gel/tag V1.0 et de la publication du frontend statique sur Vercel pour Abyss Showcase. **Ne pas annoncer de publication Vercel ni de validation esthétique exhaustive sans déploiement ou inspection observée.**

## Chantier complémentaire D5.1 — suite de la revue visuelle

La revue manuelle des cinq vues et de la fiche documentaire a mis en évidence des retouches de densité, des débordements, des statuts peu explicites et le besoin d'une aide intégrée. Les observations et corrections sont détaillées dans [PLAN-D51.md](PLAN-D51.md) ; elles ne remettent pas en cause la recette fonctionnelle D5 précédente.

Sur `work/d51-ux-ui-final-polish` : CSS de compaction et de défilement interne, onglets sticky, schéma d'états/contextes, libellés métier, analyse sourcée du rejet, FAQ locale déterministe et présentation des citations. **La recette fonctionnelle D5.1 a réussi le 10 novembre 2026** avec `scripts/verify-d51.ps1` : 58/58 tests Django, 13/13 Vitest, 4/4 Playwright Chromium, build Vite/TypeScript, SQL D3 (15 factures, 1 344 EUR TTC), modèle local RAG D4 (120 EUR cité, abstention, injection refusée). Le test D5.1 parcourt les cinq vues à 1920×993, 1649×928, 1440×900 et 390×844 et ne détecte aucun dépassement de largeur au niveau testé. **Preuve terminale : `D5.1 LOCAL OK`.** Les captures produites par Playwright doivent encore être examinées humainement ; aucune fusion V1.0, gel visuel, tag ni publication front n'est annoncée à cette étape.


### D5.1 — Recette finale après correctif de la FAQ et compacité (10 novembre 2026)

Journal local Windows/Docker transmis après mise à jour de la branche au commit `1cd90f0` : contrôles statiques Django `D5 STATIC OK`, **58/58 tests Django**, réconciliation D3 **15 factures / 7 documents acceptés / 2 rejetés / 1 344 EUR TTC**, `D4 LOCAL VERIFIED` (Ollama/Chroma, citation facture 120 EUR, abstention et injection refusée), santé API/React, `tsc -b`, build Vite, **13/13 Vitest**, et **4/4 Playwright Chromium** (51,8 s). Les scénarios incluent la FAQ produit corrigée, les cinq vues aux quatre formats initiaux et le viewport CSS compact **1320×742**, contrôlant aussi les débordements verticaux. Le script termine explicitement sur **`D5 LOCAL OK` et `D5.1 LOCAL OK`**. Les deux blocages précédents ont disparu. **Revue visuelle des nouvelles captures encore nécessaire avant fusion ou gel de V1.0.**

## Nouvelle exécution du 10 novembre — 58/58 Django, 13/13 Vitest, 3/4 Playwright

La recette locale Windows a effectivement été relancée après les ajustements du composeur/notification, avec mise à jour Git de `1cd90f0` vers `1395390`. D1–D5 backend validés : `D5 STATIC OK`, 58 tests Django passés, D3 SQL réconcilié (15 factures, 7 documents acceptés, 2 rejetés, 1 344 EUR TTC), D4 RAG réel vérifié, TypeScript/build Vite réussis, 13/13 Vitest. Playwright : démo publique, mobile et parcours local avec citations réussis, mais le scénario d'intégration des cinq vues a échoué sur le contrôle **visibilité intégrale du pied du composeur** à 1320×742 CSS : `toBeInViewport({ratio: 0.99})` a reçu **0,3461538553**. Fin du script par exception, pas de `D5.1 LOCAL OK`.

Diagnostic CSS : la règle de réduction de marges préservait `height:100%` et `flex:1 1 auto` sur la page de l'assistant, puis `height:100%` sur son panneau principal ; la combinaison peut allouer une hauteur qui dépasse légèrement l'espace réellement disponible. Les autres vues compactes passent.

**Correctif supplémentaire posé :** pour les bureaux de hauteur CSS 650–800 px, la page et la grille Assistant utilisent `flex:1 1 0`, `height:auto`, `min-height:0`, avec composition à hauteur extensible plutôt qu'à hauteur en pourcentage ; la conversation conserve son défilement interne et le composeur ne rétrécit pas. Le test Playwright écrit désormais toujours la capture du viewport **avant** l'assertion, et inclut des mesures des rectangles (`workspace`, `page`, `grid`, `main`, `composer`, `composeFooter`) en cas d'échec, pour arrêter les corrections à l'aveugle.

**Statut** : correctif enregistré sur la PR #7, mais **pas encore retesté en conditions réelles** ; relancer `scripts/verify-d51.ps1` avec la dernière branche. Ne pas fusionner, figer ou publier tant que le 4e scénario ne passe pas.

## Recette du 10 novembre — correction ciblée de la grille parent

Nouvelle recette locale Windows au commit `4d37906` : build/TypeScript réussis, **58/58 Django**, D3 à **1 344 EUR TTC**, D4 RAG vérifié, **13/13 Vitest**, **3/4 Playwright**. Le dernier scénario continue d'échouer sur le composeur Assistant à `1320×742` CSS, mais les mesures géométriques expliquent désormais **pourquoi** :

- `viewport=742` ; `.workspace-content`: `top=69,bottom=769,height=700` ;
- `.assistant-page`: `top=78,bottom=761` ; `.assistant-grid`: `top=152,bottom=761` ;
- `.assistant-compose`: `top=668,bottom=760`, `.compose-footer`: `top=738,bottom=751`.
- Le contenu déborde parce que **la rangée implicite de `.app-shell` grandit à la hauteur intrinsèque du workspace** (769 px) plutôt qu'à la hauteur du viewport (742 px), puis `overflow:hidden` la coupe. Les sous-composants et leurs marges ne sont plus la cause première.

**Correctif parent appliqué :** `frontend/src/styles.css` fixe explicitement la rangée de la grille générale `.app-shell` à `minmax(0, 1fr)`, et `.workspace` à `min-height:0`. Les cinq vues utilisent ainsi la hauteur du viewport disponible (la topbar garde ses 69 px), sans réduire ni masquer les champs de l'assistant. La navigation mobile `display:block` demeure inchangée.

**Playwright renforcé :** la boucle de toutes les vues et résolutions de bureau exige maintenant `workspaceBottom <= viewportHeight + 1`, en plus du test `compose-footer` entièrement visible à 1320×742. En cas d'échec, les coordonnées `.app-shell` et `.workspace` sont également enregistrées. La capture est conservée même lorsque l'assertion échoue.

**Statut :** correctif enregistré dans la PR #7, sans fusion/publication. Nouvelle exécution de `scripts/verify-d51.ps1` requise sur ce commit. Le précédent `D5.1 LOCAL OK` n'incluait pas ce test renforcé.

## D5.1 — Réussite de la recette après correction du workspace parent (10 novembre 2026)

Exécution utilisateur sur `163f7a7` : **58/58 tests Django, D3 SQL 1 344 EUR TTC, D4 Ollama/Chroma/RAG cité, build TypeScript/Vite, 13/13 Vitest, 4/4 scénarios Playwright Chromium (56,0 s)**. Le test d'absence de dépassement de la grille parent et celui de visibilité intégrale du composeur de l'assistant à 1320×742 passent. Sorties explicites `D5 LOCAL OK` et `D5.1 LOCAL OK`. **Il n'y a plus de blocage technique de recette ; validation de la dernière capture de l'Assistant encore distincte avant fusion et gel V1.0.**
