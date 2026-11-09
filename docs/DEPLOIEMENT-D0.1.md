# DocuMind D0.1 — Contrat de déploiement et budget 0 €

## Décision
- Développement Full Stack **local** : Django REST + PostgreSQL 16 dans Docker Compose.
- **Démo publique Render gratuite** : service Web Django D1 en lecture seule et trois fiches de documents strictement fictives, avec SQLite local **éphémère**.
- Le frontend public complet React/TypeScript sera conçu et testé dans les lots suivants, avant clôture V1.
- Ne déclarer **aucune base Render Postgres payante ou temporaire** dans le Blueprint.
- Les traitements Airflow, Metabase et Ollama restent locaux pour la V1 tant qu'aucun hébergement gratuit viable n'est démontré.
- Une option PostgreSQL externe gratuite pourra remplacer le stockage éphémère, après vérification de ses conditions.

## Pourquoi cette séparation ?
Render permet les services Web gratuits, mais les instances gratuites se mettent en veille après 15 minutes d'inactivité et la base de données gratuite Render Postgres **expire après 30 jours**. Le stockage local de la plateforme est réinitialisé lors des redémarrages et redéploiements.

Pour éviter une surprise, le mode public doit être **read-only**, sans document utilisateur, et se réinitialiser automatiquement via `seed_demo`. L'API et la base PostgreSQL locale sont de véritables composants, mais la démo publique ne garantit pas de stockage durable.

## Configuration Render
1. Connecter le dépôt GitHub `sogoyou8/DocuMind` à Render.
2. Utiliser le Blueprint `render.yaml` : **un seul Web Service**, `plan: free`, **aucune base créée**.
3. Laisser Render générer `DJANGO_SECRET_KEY`; conserver `DOCUMIND_DEMO_READONLY=1`.
4. Vérifier `/api/v1/health/`, `/api/v1/documents/`, `/api/v1/overview/`, `/api/v1/docs/`.
5. Vérifier l'impossibilité d'envoyer un POST, la remise à zéro après redémarrage et les limites d'inactivité.
6. Ne renseigner un éventuel `DATABASE_URL` que vers une ressource autorisée et gratuite après vérification.

## Critères de sortie D1
- API Django réelle, migration SQL et contrôles exécutés sur PostgreSQL local/CI.
- URL Render publique retournant 200 sur le healthcheck.
- Catalogue de fiches de démonstration correctement distinguées des vraies extractions.
- Écriture bloquée en public ; aucun secret ni fichier réel exposé.
- Aucune carte de paiement, ni abonnement, ni service payant créé.

## Limites acceptées
- Réveil lent d'un service gratuit endormi.
- Aucune persistance des changements sur le mode démo jetable.
- Pas d'Airflow, Metabase, ChromaDB ni Ollama publiquement exécutés à D1.
- Pas de promesse de disponibilité 24/7.

## Option recommandée pour la démo durable : Render Free + Neon Free

Neon propose un PostgreSQL gratuit sans date d'expiration fixe (dans les limites du plan). Utiliser **la formule Free de Neon uniquement**, vérifier l'absence de frais et ne pas ajouter de moyen de paiement facultatif. En novembre 2026, les limites publiées sont 1 Go par projet et 100 CU-heures/mois. Après épuisement des quotas, les requêtes peuvent être suspendues, mais le stockage ne disparaît pas à 30 jours comme Render Free Postgres.

Pour activer le **véritable backend PostgreSQL dans la démo Render** :
1. Créer un projet PostgreSQL en plan gratuit chez Neon, sans données personnelles réelles.
2. Dans Render, conserver le Web Service `plan: free` du Blueprint.
3. Renseigner `DATABASE_URL` dans les variables d'environnement **secrètes de Render**, avec la chaîne PostgreSQL Neon et SSL (pas dans Git, une capture ni ce chat).
4. Maintenir `DOCUMIND_DEMO_READONLY=1` : le public lit des données fictives, mais ne dépose pas de documents.
5. Redéployer et vérifier les migrations, le healthcheck, les fiches synthétiques, le réveil à froid et l'absence d'accès en écriture.

Par défaut, le Blueprint fonctionne **sans Neon** en SQLite jetable pour ne pas bloquer la première démonstration. L'option Neon est un choix explicite d'hébergement PostgreSQL, non activé automatiquement.

## Mise en ligne effective du socle D1 (9 novembre 2026)

- Blueprint `exs-dbp0l8mgekts73a9pd40`, déploiement approuvé le 9 novembre 2026.
- Service `documind-d1-api-htpg`, service ID `srv-dbp0mkugekts73a9t7q0`, région Francfort, **plan Render Free**.
- Adresse publique : https://documind-d1-api-htpg.onrender.com
- Validation Render : build réussi, migrations SQLite réalisées, `seed_demo` effectué, serveur Gunicorn démarré et healthcheck HTTP 200, état `live`.
- Aucune base Render PostgreSQL créée. Les données publiques restent des exemples synthétiques non persistants.
- **Point de vigilance** : Render peut mettre en veille les instances gratuites ; une première requête peut être lente. Un test HTTP externe complet GET/POST est fourni dans `scripts/verify-d1-render.ps1`, et doit être exécuté pour ajouter une preuve indépendante des seuls healthchecks Render.

Le backend public **n'est pas l'application métier V1 complète**. Son interface React, les traitements Airflow/Metabase et le RAG restent prévus dans les étapes suivantes.
