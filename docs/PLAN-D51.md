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
