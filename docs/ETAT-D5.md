# DocuMind — D5 : interface React, QA de bout en bout et préparation V1.0

**État du code : implémentation sur `work/d5-react-v1-cockpit`, recette Docker et tests navigateur encore à confirmer.** D0 à D4 ont déjà été validés et fusionnés. Ne pas fusionner D5 ou annoncer une V1.0 validée tant que la ligne finale `D5 LOCAL OK` et la revue des captures ne sont pas obtenues.

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

- [ ] 58 tests Django D1–D5 réussis dans le service IA/PostgreSQL, sans test D5 ignoré.
- [ ] API Django/OpenAPI/migrations et contrôle CSRF réussis.
- [ ] Indicateurs D3 cohérents, factures rejetées exclues, 1 344 EUR TTC fictifs préservés.
- [ ] Index D4 idempotent, modèle local répond avec citation à `DM-2026-001` (120 EUR) et refuse les références inconnues.
- [ ] TypeScript strict, build Vite et tests Vitest réussis.
- [ ] Playwright grand écran + mobile et parcours local authentifié + source IA réussis.
- [ ] Captures examinées : lisibilité 1920×993, 1440×900 et 390×844 ; absence de superposition et de débordement.
- [ ] Contrôles des permissions et de confidentialité, notamment sur Render, sans régression.
- [ ] Fusion GitHub puis gel V1.0 documenté **seulement après** les preuves ci-dessus.

**Préparation actuelle :** les fichiers de code, les tests automatiques et la recette sont prêts sur la branche D5, mais aucune exécution réelle `npm build` ou Playwright sur l'ordinateur utilisateur n'a encore été reçue. Les comptes de tests et les sommes sont des attentes fondées sur les tests existants et les fichiers fictifs, pas des validations observées.

## Prochaines décisions après tests

Si la recette réussit, vérifier visuellement les captures d'écran et les parcours, corriger les défauts, fusionner la PR D5 dans `main`, vérifier Render Free et décider séparément de publier le frontend statique sur Vercel pour Abyss Showcase. **Ne pas annoncer la publication Vercel tant qu'aucun déploiement n'a été créé et vérifié.**
