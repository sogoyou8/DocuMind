export type DocState = "RECEIVED" | "VALIDATING" | "ACCEPTED" | "INDEXED" | "REJECTED";
export type DocType = "PDF" | "CSV" | "XLSX";

export type Session = {
  mode: "synthetic-demo" | "local";
  authenticated: boolean;
  username: string | null;
  operator: boolean;
  ai_enabled: boolean;
  csrf_token: string;
};

export type Overview = {
  mode: "synthetic-demo" | "local";
  total: number;
  received: number;
  rejected: number;
  processed: number;
  airflow_enabled: boolean;
  ai_enabled: boolean;
  note: string;
};

export type Document = {
  id: string;
  original_name: string;
  file_type: DocType;
  sha256: string;
  size_bytes: number;
  state: DocState;
  source: "DEMO" | "UPLOAD";
  created_at: string;
};

export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type Run = {
  id: string;
  document: string;
  pipeline_version: string;
  status: "RUNNING" | "SUCCEEDED" | "REJECTED" | "FAILED";
  attempt_number: number;
  error_summary: string;
  started_at: string;
  finished_at: string | null;
};

export type RecordRow = {
  id: string;
  document: string;
  run: string;
  source_locator: string;
  raw_fields: Record<string, unknown>;
  normalized_fields: Record<string, unknown>;
};

export type Issue = {
  id: string;
  run: string;
  record: string | null;
  source_locator: string;
  code: string;
  severity: string;
  field_name: string;
  message: string;
  created_at: string;
};

export type Invoice = {
  id: string;
  document: string;
  run: string;
  record: string;
  source_locator: string;
  supplier_name: string;
  invoice_number: string;
  issued_on: string;
  currency: string;
  subtotal: string;
  tax: string;
  total: string;
};

export type Audit = {
  id: string;
  document_id: string;
  document_name: string;
  action: string;
  actor: string | null;
  created_at: string;
};

export type Currency = {
  currency: string;
  invoice_count: number;
  supplier_count: number;
  subtotal: string;
  tax: string;
  total: string;
};

export type Monthly = {
  month: string;
  currency: string;
  invoice_count: number;
  total: string;
};

export type Supplier = {
  supplier_name: string;
  currency: string;
  invoice_count: number;
  total: string;
};

export type Analytics = {
  available: boolean;
  reason: string | null;
  currencies: Currency[];
  monthly: Monthly[];
  suppliers: Supplier[];
  statuses: { state: string; count: number }[];
  issues: { code: string; severity: string; count: number }[];
};

export type Citation = {
  id: string;
  document_id: string;
  document: string;
  source_locator: string;
  excerpt: string;
};

export type AssistantAnswer = {
  status: "answered" | "abstained";
  answer: string;
  citations: Citation[];
};

export type AssistantStatus = {
  mode: "local-only";
  enabled: boolean;
  embedding_model: string;
  generation_model: string;
  indexed_chunks: number;
};

export type ProcessResult = {
  run_id: string;
  status: string;
  attempt_number: number;
  skipped: boolean;
  records_count: number;
  issues_count: number;
  invoices_count: number;
};

export type IndexResult = { indexed_chunks: number; skipped: boolean };
export type Tab = "overview" | "documents" | "analytics" | "assistant" | "activity";
