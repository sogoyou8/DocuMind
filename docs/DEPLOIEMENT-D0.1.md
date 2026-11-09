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
