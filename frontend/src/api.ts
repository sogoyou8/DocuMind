import type {
  Analytics, AssistantAnswer, AssistantStatus, Audit, Document,
  IndexResult, Invoice, Issue, Overview, Page, ProcessResult,
  RecordRow, Run, Session,
} from "./types";

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = {
  method?: "GET" | "POST";
  body?: FormData | Record<string, unknown>;
  csrf?: string;
  timeout?: number;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  if (!path.startsWith("/api/v1/") || path.startsWith("//")) {
    throw new ApiError("Chemin API invalide.", 400);
  }
  const method = options.method ?? "GET";
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.csrf) headers["X-CSRFToken"] = options.csrf;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeout ?? 20000);
  try {
    const response = await fetch(path, {
      method,
      headers,
      credentials: "same-origin",
      body: options.body
        ? options.body instanceof FormData
          ? options.body
          : JSON.stringify(options.body)
        : undefined,
      signal: controller.signal,
    });
    const contentType = response.headers.get("content-type") ?? "";
    const data: unknown = contentType.includes("application/json")
      ? await response.json()
      : null;
    if (!response.ok) {
      const record = data && typeof data === "object"
        ? data as Record<string, unknown> : {};
      const detail = typeof record.detail === "string"
        ? record.detail
        : typeof record.file === "string"
          ? record.file : Array.isArray(record.file)
            ? String(record.file[0]) : `Erreur API (HTTP ${response.status}).`;
      throw new ApiError(detail, response.status);
    }
    if (data === null) throw new ApiError("Le serveur n'a pas renvoyé de JSON.", 502);
    return data as T;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (controller.signal.aborted) throw new ApiError("Délai de réponse dépassé.", 408);
    throw new ApiError("Impossible de joindre DocuMind. Vérifie le service local.", 503);
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  session: () => request<Session>("/api/v1/session/"),
  login: (username: string, password: string, csrf: string) =>
    request<{ authenticated: boolean }>("/api/v1/session/login/", {
      method: "POST", csrf, body: { username, password },
    }),
  logout: (csrf: string) =>
    request<{ authenticated: boolean }>("/api/v1/session/logout/", {
      method: "POST", csrf, body: {},
    }),
  overview: () => request<Overview>("/api/v1/overview/"),
  documents: (page = 1) =>
    request<Page<Document>>(`/api/v1/documents/?page=${Math.max(1, Math.trunc(page))}`),
  document: (id: string) => request<Document>(`/api/v1/documents/${encodeURIComponent(id)}/`),
  invoices: (id?: string) =>
    request<Page<Invoice>>(`/api/v1/invoices/${id ? `?document=${encodeURIComponent(id)}` : ""}`),
  records: (id?: string) =>
    request<Page<RecordRow>>(`/api/v1/records/${id ? `?document=${encodeURIComponent(id)}` : ""}`),
  issues: (id?: string) =>
    request<Page<Issue>>(`/api/v1/quality-issues/${id ? `?document=${encodeURIComponent(id)}` : ""}`),
  runs: (id?: string) =>
    request<Page<Run>>(`/api/v1/processing-runs/${id ? `?document=${encodeURIComponent(id)}` : ""}`),
  audit: (id?: string) =>
    request<{ count: number; results: Audit[] }>(`/api/v1/audit/${id ? `?document=${encodeURIComponent(id)}` : ""}`),
  analytics: () => request<Analytics>("/api/v1/analytics/"),
  upload: (file: File, csrf: string) => {
    const body = new FormData();
    body.append("file", file);
    return request<Document>("/api/v1/documents/", { method: "POST", body, csrf, timeout: 35000 });
  },
  process: (id: string, csrf: string, force = false) =>
    request<ProcessResult>(`/api/v1/documents/${encodeURIComponent(id)}/process/`, {
      method: "POST", body: { force }, csrf, timeout: 90000,
    }),
  index: (id: string, csrf: string) =>
    request<IndexResult>(`/api/v1/documents/${encodeURIComponent(id)}/index/`, {
      method: "POST", body: {}, csrf, timeout: 150000,
    }),
  assistantStatus: () => request<AssistantStatus>("/api/v1/assistant/status/"),
  ask: (question: string, csrf: string) =>
    request<AssistantAnswer>("/api/v1/assistant/ask/", {
      method: "POST", csrf, body: { question }, timeout: 150000,
    }),
};
