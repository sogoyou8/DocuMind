# D5.1 — Finition UX/UI transversale, issue de la revue visuelle du 10 novembre 2026

Statut : chantier isolé sur `work/d51-ux-ui-final-polish` ; aucune modification des modèles Django, pipelines D2, vues SQL D3, RAG D4, secrets ni déploiement public. Les cinq vues et le panneau documentaire ont été examinés sur captures réelles. La qualité fonctionnelle D5 reste la base (58 tests Django, 3 E2E Playwright, `D5 LOCAL OK`).

## Corrections à réaliser et critères de recette

| ID | Emplacement | Observation étayée par les captures | Modification technique | Critère de réussite |
|---|---|---|---|---|
| P0-01 | Analyse & KPI | Débordement horizontal et légende du donut coupée à droite sur 1649×928 | Colonnes `minmax(0, …)`, tailles flex autorisées à rétrécir, donut/ligne de légende adaptés | Aucun scroll horizontal à 1920×993, 1649×928, 1440×900, 390×844 ; trois états visibles |
| P0-02 | Assistant IA | Pied de page visible derrière le composeur, avertissement latéral touchant le bas | Grille à hauteur bornée, conversation scrollable, composition ancrée, pied de page exclu de cette vue | Texte d'aide, champ et avertissement sans superposition ; messages consultables |
| P0-03 | Historique | Un événement de rejet est associé au même pictogramme vert qu'un succès | Couleurs et icônes déterminées par type d'événement, jamais par position | Un rejet est orange/rouge, une réussite verte, une initialisation neutre |
| P1-01 | Vue d'ensemble | Hero long + bas de page hors écran | Réduction proportionnelle hero/KPI/graphiques, regroupement équilibré ; scroll de secours lorsque l'écran est trop bas | Les sept modules restent lisibles à 1920×993 ; ni découpage ni texte tronqué à 390px |
| P1-02 | Documents | En-tête et filtres disparaissent lorsque l'utilisateur descend les 9 lignes | Catalogue à défilement interne, barre d'outils et colonnes persistantes ; lignes plus denses | Recherche, filtres, colonnes et pagination restent utilisables sur bureau |
| P1-03 | Fiche documentaire | Onglets disparaissent au défilement ; boutons de traitement incohérents | Onglets `position: sticky`; « Déjà indexé » non cliquable, indexation absente pour rejeté, retraitement contextualisé | Actions alignées sur `RECEIVED/REJECTED/ACCEPTED/INDEXED` |
| P1-04 | Documents, Historique | Noms techniques `subtotal/tax`, `RAG_INDEXED`, dates ISO | Libellés français maintenus via dictionnaires explicites ; date et heure locale pour audit ; conserver valeurs/codes bruts consultables | Pas de codes anglais utilisés comme titres courants ; origine technique accessible |
| P1-05 | Document rejeté | `TOTAL_MISMATCH` a seulement un message générique | Résoudre la ligne extraite reliée à l'erreur ; HT+TVA, TTC déclaré, écart calculés à partir du record quand ces champs sont présents | 20+4=24, TTC déclaré 30, écart 6 ; jamais de valeurs calculées sans source |
| P1-06 | Assistant IA | Les questions « Que peux-tu faire ? » et « Quels types de documents acceptes-tu ? » déclenchent une abstention RAG | Aide locale déterministe, strictement sur le logiciel, distincte des réponses documentaires, sans citation inventée | Questions d'aide traitées sans Ollama ; question sur facture inconnue conserve l'abstention |
| P1-07 | Assistant IA | Réponse numérique « 120.00 » peu lisible ; citation longue et brute | Format montant EUR TTC seulement si la question concerne le TTC et la source l'établit ; citation résumée, détail technique consultable | 120,00 € TTC affiché pour DM-2026-001 ; lien vers fiche fonctionnel |
| P2-01 | Vue d'ensemble, Analyse | Axe des ordonnées trop discret, une seule graduation | Quatre repères de valeurs et graphique adaptatif ; libellés/unités lisibles | 5 mois visibles, 0–max et graduations, sans valeur financière inventée |
| P2-02 | Ensemble des vues | Textes secondaires trop discrets, cartes trop hautes | Contraste et typographie secondaire relevés ; densité mesurée sur bureau | Lisible sans perdre la hiérarchie ; responsive mobile conservé |
| P2-03 | Historique | Liste longue avec espaces vides et recherche perdue | Timeline plus dense, zone de scroll interne, recherche sticky, vrai timestamp ; limite API 40 explicitée | Consultation des 25 événements en gardant recherche et titre |
| P2-04 | E2E | Les trois tests D5 valident la fonction, pas les retouches multi-résolution | Ajouter assertions frontend et Playwright sur mises en page, événements et aide RAG | `typecheck`, `build`, `Vitest`, `Playwright`, D5 backend restent au vert |

## Contraintes et limites explicites

- **Pas de fausses données** : jamais de montant, facture, statut d'indexation, réponse IA ou action inventés. Les explications automatiques reposent sur le code et les valeurs extraites, pas sur un LLM.
- **Sécurité** : les questions documentaires passent par le moteur local RAG inchangé, les accès et permissions passent par Django. L'aide générale sur l'application ne doit pas masquer les questions documentaires ni générer de citations factices.
- **Responsive** : priorité cockpit bureau (dont 1920×993 et captures 1649×928), mais repli en défilement naturel sur hauteur insuffisante et mobile 390×844, sans scroll horizontal.
- **Workflow** : commits sur branche isolée, PR en brouillon, aucune fusion ni publication sans exécution locale des contrôles et revue de captures.
- **Tests attendus** : `npm run typecheck`, `npm run build`, `npm test`, `npm run test:e2e`, recette existante `scripts/verify-d5.ps1` et nouvelle validation des dimensions/états.

## Première recette D5.1 — échec navigateur identifié et correctif

La première recette Windows/Docker a confirmé **58/58 Django**, **13/13 Vitest**, build TypeScript/Vite, réconciliation **1 344 EUR TTC** et vérification D4. Playwright a obtenu **2/4** : la démo bureau et mobile sont passées ; le navigateur ne trouvait pas « Guide de l'application » après la question « Que peux-tu faire ? », et mesurait **12 px** de débordement horizontal interne sur Analyse & KPI à 1440×900.

Les journaux Docker indiquaient `documind-web-1 Running` pendant la recette : le serveur Vite était réutilisé sans redémarrage après le changement de branche Git, contrairement au conteneur de test Playwright qui lisait les nouveaux scénarios. Les deux défauts correspondent aux fonctionnalités/styles ajoutés à D5.1 et étaient présents dans D5. **Hypothèse principale : Vite servait les anciens modules en cache**, à confirmer par la nouvelle recette ; une régression CSS indépendante n'est pas exclue tant qu'un nouveau test navigateur n'a pas réussi.

Correctif conservateur dans `scripts/verify-d5.ps1` sur la branche D5.1 : vider uniquement le cache Vite optimisé `/app/node_modules/.vite`, puis **redémarrer le service `web`** avant les tests. Les volumes PostgreSQL/Chroma/Metabase/Ollama sont préservés. L'E2E vérifie désormais la présence du nouveau bouton « Découvrir DocuMind » dès l'arrivée sur l'assistant, puis confirme que le guide ne déclenche aucune requête RAG et qu'une facture déclenche toujours l'API source. L'aide est testée **avant** la requête longue Ollama.

Ne pas annoncer `D5.1 LOCAL OK` avant une seconde recette réussie et la revue des captures. L'état GitHub reste une PR en brouillon.

## Deuxième recette D5.1 — succès fonctionnel (10 novembre 2026)

Le journal complet Windows/Docker reçu après redémarrage du serveur Vite constate : `D5 STATIC OK`, vérifications Django sans erreur, **58/58 tests Django OK**, `D3 SQL VERIFIED` (15 factures fictives acceptées, 7 documents acceptés, 2 rejetés, 1 344 EUR TTC et cinq périodes), `D4 LOCAL VERIFIED` (Ollama/Chroma, citation sur 120 EUR, abstention, refus d'injection), santé API/React OK, TypeScript strict, **build Vite réussi**, **13/13 tests Vitest réussis** et **4/4 scénarios Playwright Chromium réussis en 30,7 s**.

Les scénarios E2E ayant réussi incluent : démo publique sans KPI inventés, navigation mobile, parcours local réel Django/PostgreSQL/SQL/RAG avec preuve et guide déterministe sans requête LLM, puis les cinq vues sur **1920×993, 1649×928, 1440×900 et 390×844** avec vérification d'absence de débordement horizontal et états de rejet/anomalie. Le script a émis **`D5 LOCAL OK` puis `D5.1 LOCAL OK`**.

Cette réussite après nettoyage du cache et redémarrage Vite appuie l'hypothèse de modules obsolètes servis lors du premier essai ; elle ne permet pas d'isoler à elle seule le facteur exact. Le nouveau test vérifie explicitement le raccourci d'aide afin de détecter ce cas plus tôt.

**Reste à faire :** regarder les captures produites sous `frontend/test-results/` et valider visuellement la densité/finition des cinq vues, puis fusionner cette PR après acceptation de cette dernière revue. L'exécution automatique ne prouve pas à elle seule le niveau esthétique du rendu. Aucun déploiement Vercel, tag V1.0 ou fusion n'a été réalisé.

## Revue des captures du 10 novembre — finition complémentaire à revalider

Vingt captures manuelles transmises, couvrant les cinq vues, l'assistant et les panneaux documentaires. Les améliorations D5.1 sont **visiblement présentes** : libellés de dates/montants, réconciliation D3 (1 120 HT + 224 TVA = 1 344 TTC), rejet TTC 24 attendu / 30 déclaré / 6 d'écart, boutons par statut, journal d'audit horodaté avec événements verts/orange/gris, courbes avec graduations, plus de débordement horizontal visible sur Analyse & KPI. Le composeur IA ne chevauche plus le pied de page. Onglets de détail persistants observés.

**Reste identifié sur ces captures** : (1) la Vue d'ensemble et Analyse & KPI nécessitent encore de faire défiler la page à la taille d'affichage présentée (images 1649×928), alors que le mode compact précédent était limité à `@media (min-width:1360px) and (min-height:850px)` en *pixels CSS*, susceptibles de différer de la résolution des captures en fonction du zoom et de l'échelle du système ; (2) la demande exacte `en quoi consiste cette app ?` entraîne une abstention malgré l'aide réussie `que peux tu faire ?`.

**Correctifs ajoutés sur la même branche, après la précédente recette réussie :** élargissement mesuré du cockpit compact aux bureaux à largeur CSS ≥1200 et hauteur CSS ≥730, en gardant une grille mono-écran à quatre zones pour la Vue d'ensemble, trois zones d'analyse et défilements **internes** pour documents/journal ; repli en défilement naturel si la hauteur CSS est inférieure à 730 px. Ajout d'une réponse déterministe décrivant DocuMind, uniquement pour les formulations de découverte de l'application ; la recherche documentaire et son abstention sont inchangées. Tests Vitest pour les formulations exactes et confusions avec les vraies questions documentaires ; tests Playwright étendus au contrôle **vertical** et à 1320×742 px CSS.

**Statut de la dernière passe : code et tests mis à jour, nouvelle recette `scripts/verify-d51.ps1` et contrôle de capture requis.** Le `D5.1 LOCAL OK` observé précédemment reste une preuve pour l'ancien commit, **pas** pour ces derniers correctifs. Ne pas fusionner ou publier tant que cette recette et le nouvel affichage n'ont pas été confirmés.

## Recette après les retouches visuelles — Vitest à corriger

Lors de l'exécution locale de `scripts/verify-d51.ps1` sur le commit `4dd0099`, le journal transmis a validé la compilation Vite/TypeScript, **58/58 tests Django**, la réconciliation D3 à **1 344 EUR TTC**, et le vrai moteur RAG D4. La recette s'est arrêtée à **12/13 Vitest** avant Playwright.

Échec exact : `applicationHelp("En quoi consiste ce document accepté ?")` produisait l'aide sur les PDF/CSV/XLSX au lieu de `null`. La cause était une règle trop large `/(document|fichier).*(accept|import|...)/` qui interprétait la mention d'un *document accepté particulier* comme une question sur les *formats acceptés*.

Correctif : classification des formats restreinte aux questions explicitement orientées vers les catégories ou les possibilités d'import. Les questions sur un document particulier restent adressées au RAG vérifiable. Tests Vitest ajoutés pour « Quels documents sont acceptés ? », l'import d'un PDF, « En quoi consiste ce document accepté ? » et « Que contient ce document accepté ? ». Vérification statique des expressions effectuée sur les formulations ; **la suite Docker/Vitest/Playwright doit encore être relancée** sur ce nouveau commit. Aucun changement D1–D4, aucune fusion ni publication.

## Recette D5.1 après derniers correctifs — SUCCÈS (10 novembre 2026)

Journal Windows/Docker confirmé après `git pull` de `4dd0099` à `1cd90f0` : 58/58 Django, réconciliation SQL D3 (15 factures, 7 documents acceptés, 2 rejetés, 1 344 EUR TTC), vrai RAG D4 (citation 120 EUR, abstention, injection refusée), build React TypeScript/Vite, **13/13 Vitest**, **4/4 Playwright Chromium (51,8 s)**. Les scénarios parcourent les cinq vues sur desktop et mobile et vérifient le débordement horizontal ainsi que le **scroll vertical externe** pour Vue d'ensemble / Analyse & KPI sur les résolutions de bureau, avec un viewport CSS compact **1320×742**. La réponse déterministe à « on quoi consiste cette app ? » et la distinction des questions sur un document particulier ont passé la recette. Fin de script : **`D5 LOCAL OK`, `D5.1 LOCAL OK`**.

Les correctifs de la FAQ et du mode compact sont donc validés techniquement. Les captures Playwright restent dans `frontend/test-results/` sur la machine locale ; leur rendu final n'a pas encore été inspecté visuellement après ce dernier changement. **Garder la PR #7 en brouillon sans fusion, gel ou publication avant revue esthétique finale.**

## Revue des cinq captures 1320×742 — dernier ajustement mineur

Captures réellement examinées : `d51-overview-1320x742.png`, `d51-documents-1320x742.png`, `d51-analytics-1320x742.png`, `d51-assistant-1320x742.png`, `d51-history-1320x742.png`. Toutes les zones métier essentielles sont présentes, la grille analytique tient dans la fenêtre sans débordement, et les listes de documents/journal restent consultables dans leur panneau par défilement interne. Les KPI, devises, légendes, filtres, dates et états demeurent cohérents avec D1–D4.

**Deux écarts UX non bloquants mais corrigés avant gel :** (1) le pied du composeur assistant est légèrement coupé par le bord inférieur à 1320×742 ; (2) la notification persistante `Session locale ouverte.` recouvre une portion des panneaux et n'était fermée que manuellement.

Correctifs complémentaires sur la même branche : compaction très ciblée du composeur et de son en-tête aux hauteurs CSS bureau 650–800 px ; fermeture automatique de la notification de succès au bout de 4,5 s, sans suppression des erreurs persistantes ; Playwright vérifie que le composeur **entier** est dans la fenêtre à 1320×742 et ferme la notification avant la capture des vues.

**Statut :** revue visuelle des cinq captures effectuée, correctifs implémentés. La recette `D5.1 LOCAL OK` précédente valide le commit antérieur seulement. Une nouvelle recette `scripts/verify-d51.ps1` est requise avant fusion ; pas de tag V1.0 ni de publication.

## Nouvelle exécution du 10 novembre — 58/58 Django, 13/13 Vitest, 3/4 Playwright

La recette locale Windows a effectivement été relancée après les ajustements du composeur/notification, avec mise à jour Git de `1cd90f0` vers `1395390`. D1–D5 backend validés : `D5 STATIC OK`, 58 tests Django passés, D3 SQL réconcilié (15 factures, 7 documents acceptés, 2 rejetés, 1 344 EUR TTC), D4 RAG réel vérifié, TypeScript/build Vite réussis, 13/13 Vitest. Playwright : démo publique, mobile et parcours local avec citations réussis, mais le scénario d'intégration des cinq vues a échoué sur le contrôle **visibilité intégrale du pied du composeur** à 1320×742 CSS : `toBeInViewport({ratio: 0.99})` a reçu **0,3461538553**. Fin du script par exception, pas de `D5.1 LOCAL OK`.

Diagnostic CSS : la règle de réduction de marges préservait `height:100%` et `flex:1 1 auto` sur la page de l'assistant, puis `height:100%` sur son panneau principal ; la combinaison peut allouer une hauteur qui dépasse légèrement l'espace réellement disponible. Les autres vues compactes passent.

**Correctif supplémentaire posé :** pour les bureaux de hauteur CSS 650–800 px, la page et la grille Assistant utilisent `flex:1 1 0`, `height:auto`, `min-height:0`, avec composition à hauteur extensible plutôt qu'à hauteur en pourcentage ; la conversation conserve son défilement interne et le composeur ne rétrécit pas. Le test Playwright écrit désormais toujours la capture du viewport **avant** l'assertion, et inclut des mesures des rectangles (`workspace`, `page`, `grid`, `main`, `composer`, `composeFooter`) en cas d'échec, pour arrêter les corrections à l'aveugle.

**Statut** : correctif enregistré sur la PR #7, mais **pas encore retesté en conditions réelles** ; relancer `scripts/verify-d51.ps1` avec la dernière branche. Ne pas fusionner, figer ou publier tant que le 4e scénario ne passe pas.
