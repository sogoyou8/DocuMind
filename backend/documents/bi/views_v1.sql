-- DocuMind D3 BI contract, PostgreSQL only.
-- One invoice / document / issue per grain; no multiplying joins.
-- This file is frozen for migration 0003. Schema 'bi' is separate from public
-- to make least-privilege read-only access possible.
CREATE SCHEMA IF NOT EXISTS bi;

CREATE OR REPLACE VIEW bi.validated_invoices AS
SELECT
    i.id AS invoice_id,
    i.document_id,
    i.run_id,
    i.record_id,
    d.original_name AS document_name,
    d.file_type,
    d.created_at AS imported_at,
    er.source_locator,
    s.id AS supplier_id,
    s.name AS supplier_name,
    i.invoice_number,
    i.issued_on,
    i.currency,
    i.subtotal,
    i.tax,
    i.total
FROM documents_invoice AS i
JOIN documents_document AS d ON d.id = i.document_id
JOIN documents_processingrun AS r
    ON r.id = i.run_id AND r.document_id = d.id
JOIN documents_extractedrecord AS er
    ON er.id = i.record_id AND er.run_id = r.id
       AND er.document_id = d.id
JOIN documents_supplier AS s ON s.id = i.supplier_id
WHERE d.source = 'UPLOAD'
  AND d.state IN ('ACCEPTED', 'INDEXED')
  AND r.status = 'SUCCEEDED';

CREATE OR REPLACE VIEW bi.document_quality AS
SELECT
    d.id AS document_id,
    d.original_name AS document_name,
    d.file_type,
    d.state AS document_state,
    d.created_at AS imported_at,
    pr.id AS run_id,
    pr.status AS run_status,
    pr.pipeline_version,
    pr.attempt_number,
    COALESCE(problems.issue_count, 0)::integer AS issue_count
FROM documents_document AS d
LEFT JOIN LATERAL (
    SELECT r.id, r.status, r.pipeline_version, r.attempt_number
    FROM documents_processingrun AS r
    WHERE r.document_id = d.id
    ORDER BY r.started_at DESC, r.id DESC
    LIMIT 1
) pr ON TRUE
LEFT JOIN LATERAL (
    SELECT COUNT(*) AS issue_count
    FROM documents_qualityissue AS q
    WHERE q.run_id = pr.id AND q.severity = 'ERROR'
) problems ON TRUE
WHERE d.source = 'UPLOAD';

CREATE OR REPLACE VIEW bi.quality_issues AS
SELECT
    q.id AS issue_id,
    d.id AS document_id,
    d.original_name AS document_name,
    d.file_type,
    d.created_at AS imported_at,
    q.source_locator,
    q.code AS issue_code,
    q.field_name,
    q.severity,
    q.message,
    q.created_at AS detected_at
FROM documents_qualityissue AS q
JOIN documents_processingrun AS pr ON pr.id = q.run_id
JOIN documents_document AS d ON d.id = pr.document_id
WHERE d.source = 'UPLOAD'
  AND pr.id = (
      SELECT r2.id
      FROM documents_processingrun r2
      WHERE r2.document_id = d.id
      ORDER BY r2.started_at DESC, r2.id DESC
      LIMIT 1
  );

CREATE OR REPLACE VIEW bi.spending_monthly AS
SELECT
    date_trunc('month', issued_on::timestamp)::date AS month,
    currency,
    COUNT(*)::integer AS invoice_count,
    COUNT(DISTINCT supplier_id)::integer AS supplier_count,
    SUM(subtotal)::numeric(18, 2) AS subtotal,
    SUM(tax)::numeric(18, 2) AS tax,
    SUM(total)::numeric(18, 2) AS total
FROM bi.validated_invoices
GROUP BY date_trunc('month', issued_on::timestamp)::date, currency;

CREATE OR REPLACE VIEW bi.spending_suppliers AS
SELECT
    supplier_id,
    supplier_name,
    currency,
    COUNT(*)::integer AS invoice_count,
    SUM(subtotal)::numeric(18, 2) AS subtotal,
    SUM(tax)::numeric(18, 2) AS tax,
    SUM(total)::numeric(18, 2) AS total
FROM bi.validated_invoices
GROUP BY supplier_id, supplier_name, currency;

CREATE OR REPLACE VIEW bi.spending_formats AS
SELECT
    file_type,
    currency,
    COUNT(*)::integer AS invoice_count,
    SUM(total)::numeric(18, 2) AS total
FROM bi.validated_invoices
GROUP BY file_type, currency;

CREATE OR REPLACE VIEW bi.currency_totals AS
SELECT
    currency,
    COUNT(*)::integer AS invoice_count,
    COUNT(DISTINCT supplier_id)::integer AS supplier_count,
    SUM(subtotal)::numeric(18, 2) AS subtotal,
    SUM(tax)::numeric(18, 2) AS tax,
    SUM(total)::numeric(18, 2) AS total
FROM bi.validated_invoices
GROUP BY currency;

CREATE OR REPLACE VIEW bi.document_status_counts AS
SELECT
    document_state,
    file_type,
    COUNT(*)::integer AS document_count
FROM bi.document_quality
GROUP BY document_state, file_type;

CREATE OR REPLACE VIEW bi.issue_code_counts AS
SELECT
    issue_code,
    severity,
    COUNT(*)::integer AS issue_count
FROM bi.quality_issues
GROUP BY issue_code, severity;
