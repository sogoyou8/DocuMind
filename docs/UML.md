# DocuMind — UML cible D0

**Diagrammes de conception** ; ne décrivent pas encore une application implémentée.

## 1. Composants

~~~mermaid
flowchart LR
 U[Utilisateur] --> WEB[React / TypeScript]
 WEB --> API[Django REST]
 API --> DB[(PostgreSQL)]
 API --> FILES[Stockage prive]
 AF[Airflow] --> WORK[Worker Pandas]
 WORK --> FILES
 WORK --> DB
 WORK --> VEC[(ChromaDB)]
 META[Metabase] --> DB
 API --> G[LangGraph]
 G --> VEC
 G --> O[Ollama local]
~~~

## 2. Classes

~~~mermaid
classDiagram
 class Document {
   UUID id
   string sha256
   string filename
   DocumentState state
 }
 class ProcessingRun {
   UUID id
   string pipelineVersion
   RunState state
 }
 class ExtractedRecord {
   UUID id
   string sourceLocator
   json normalizedFields
 }
 class QualityIssue {
   string rule
   string severity
 }
 class Supplier {
   UUID id
   string name
 }
 class Invoice {
   UUID id
   date issuedOn
   decimal subtotal
   decimal tax
   decimal total
 }
 class ChunkReference {
   string vectorId
   int page
 }
 class AuditEvent {
   string action
   datetime occurredAt
 }
 Document "1" --> "*" ProcessingRun
 ProcessingRun "1" --> "*" ExtractedRecord
 ExtractedRecord "1" --> "*" QualityIssue
 ExtractedRecord "1" --> "0..1" Invoice
 Supplier "1" --> "*" Invoice
 Document "1" --> "*" ChunkReference
 Document "1" --> "*" AuditEvent
~~~

## 3. Séquence de traitement

~~~mermaid
sequenceDiagram
 actor U as Operateur
 participant F as React
 participant A as API
 participant P as PostgreSQL
 participant D as Airflow
 participant W as Worker
 participant V as ChromaDB
 U->>F: Importer document
 F->>A: POST /documents
 A->>P: Enregistrer RECEIVED et SHA-256
 A-->>F: Identifiant
 D->>W: Pipeline de traitement
 W->>P: Extraction, controles et provenance
 alt Valide
   W->>P: ACCEPTED
   W->>V: Indexer extraits
   W->>P: INDEXED
 else Invalide
   W->>P: REJECTED + diagnostic
 end
 F->>A: GET /documents/id
 A-->>F: Statut + preuves
~~~

## 4. États

~~~mermaid
stateDiagram-v2
 [*] --> RECEIVED
 RECEIVED --> VALIDATING
 VALIDATING --> ACCEPTED
 VALIDATING --> REJECTED
 ACCEPTED --> INDEXED
 ACCEPTED --> REJECTED
 REJECTED --> VALIDATING: Relance autorisee
 INDEXED --> VALIDATING: Nouvelle version
~~~

Les cardinalités, champs et transitions exactes seront éprouvés lors de D1.
