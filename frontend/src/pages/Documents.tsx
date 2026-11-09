import { useEffect, useRef, useState } from "react";
import {
  AlertTriangle, ArrowLeft, ArrowRight, CheckCircle2, ChevronRight,
  FileCheck, FileClock, FileText, FileUp, Fingerprint, LockKeyhole,
  Search, Sparkles, Upload, X,
} from "lucide-react";
import type { Document, Page } from "../types";
import type { DocumentDetail } from "../types";
import { bytes, money, shortDate, stateLabels } from "../format";
import { EmptyState, Field, Hint, LabelPill, Pane, StatusChip } from "../components/Visuals";

const filters = [
  { id: "all", label: "Tous" },
  { id: "RECEIVED", label: "Reçus" },
  { id: "ACCEPTED", label: "Acceptés" },
  { id: "INDEXED", label: "Indexés" },
  { id: "REJECTED", label: "Rejetés" },
] as const;

type Props = {
  listing: Page<Document> | null;
  loading: boolean;
  selected: Document | null;
  detail: DocumentDetail | null;
  detailLoading: boolean;
  demo: boolean;
  operator: boolean;
  aiEnabled: boolean;
  actionBusy: string | null;
  page: number;
  onPage: (page: number) => void;
  onSelect: (doc: Document | null) => void;
  onUpload: (file: File) => Promise<void>;
  onProcess: (doc: Document, force?: boolean) => Promise<void>;
  onIndex: (doc: Document) => Promise<void>;
};

export function DocumentsView({
  listing, loading, selected, detail, detailLoading, demo, operator,
  aiEnabled, actionBusy, page, onPage, onSelect, onUpload, onProcess, onIndex,
}: Props) {
  const [filter, setFilter] = useState<(typeof filters)[number]["id"]>("all");
  const [search, setSearch] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const ref = useRef<HTMLInputElement>(null);
  const displayed = (listing?.results ?? []).filter(doc =>
    (filter === "all" || doc.state === filter) &&
    doc.original_name.toLocaleLowerCase("fr").includes(search.trim().toLocaleLowerCase("fr")),
  );
  const canUpload = !demo && operator;
  const upload = async () => {
    if (!file || actionBusy) return;
    if (file.size === 0 || file.size > 5 * 1024 * 1024 ||
        !/\.(pdf|csv|xlsx)$/i.test(file.name)) {
      setFileError("Utilise un PDF, CSV ou XLSX de 1 octet à 5 Mio.");
      return;
    }
    setFileError(null);
    try {
      await onUpload(file);
      setFile(null);
      if (ref.current) ref.current.value = "";
    } catch (error) {
      setFileError(error instanceof Error ? error.message : "L'import a échoué.");
    }
  };

  return <div className="page-stack">
    <div className="page-intro">
      <div><div className="eyebrow">DOCUMENTS / CATALOGUE</div>
        <h1>Bibliothèque documentaire</h1>
        <p>Chaque fichier, chaque décision et chaque provenance au même endroit.</p></div>
      <LabelPill kind={demo ? "info" : "good"}>{demo ? "3 exemples fictifs · lecture seule" : "PostgreSQL local"}</LabelPill>
    </div>
    <Pane className="upload-panel">
      <div className="upload-intro">
        <div className="upload-icon"><FileUp size={24}/></div>
        <div><h2>Importer un document</h2>
          <p>PDF textuel, CSV ou Excel XLSX · 5 Mio maximum · contrôle de signature côté serveur</p></div>
      </div>
      {canUpload ? <div className="upload-controls">
        <label className="file-picker" htmlFor="doc-upload">
          <Upload size={16}/><span>{file ? file.name : "Choisir un fichier"}</span>
        </label>
        <input ref={ref} id="doc-upload" className="sr-only" type="file" accept=".pdf,.csv,.xlsx"
          onChange={event => {setFile(event.target.files?.[0] ?? null);setFileError(null);}}/>
        <button className="btn btn-primary" type="button" disabled={!file || Boolean(actionBusy)}
          onClick={() => void upload()}>
          <FileUp size={16}/>{actionBusy === "upload" ? "Import en cours…" : "Importer"}
        </button>
      </div> : <div className="upload-disabled"><LockKeyhole size={15}/>
        {demo ? "L'import est désactivé dans la démonstration publique." : "Le rôle opérateur est nécessaire pour importer des fichiers."}</div>}
      {fileError && <div className="inline-error" role="alert">{fileError}</div>}
    </Pane>

    <Pane className="document-table-pane" title="Catalogue" subtitle={listing
      ? `${listing.count} document(s) au total · résultats de la page ${page}`
      : "Chargement depuis l'API"} aside={<FileText className="muted-icon" size={18}/>}>
      <div className="table-toolbar">
        <label className="search-field"><Search size={17}/>
          <input type="search" value={search} onChange={event => setSearch(event.target.value)}
            placeholder="Rechercher sur cette page…" aria-label="Rechercher un document sur la page"/>
        </label>
        <div className="filter-pills" aria-label="Filtrer selon l'état">
          {filters.map(f => <button type="button" key={f.id}
            className={`filter-pill ${filter === f.id ? "selected" : ""}`}
            aria-pressed={filter === f.id} onClick={() => setFilter(f.id)}>{f.label}</button>)}
        </div>
      </div>
      <div className="table-overflow">
        <table className="data-table">
          <thead><tr><th>Document</th><th>État</th><th>Import</th><th>Taille</th><th className="end-cell">Détails</th></tr></thead>
          <tbody>
            {displayed.map(doc => <tr key={doc.id}>
              <td><button className="table-doc" type="button" onClick={() => onSelect(doc)}>
                <span className={`file-badge file-${doc.file_type.toLowerCase()}`}>{doc.file_type}</span>
                <span><strong title={doc.original_name}>{doc.original_name}</strong>
                  <small>{doc.source === "DEMO" ? "Métadonnées fictives" : "Source locale vérifiable"}</small></span>
              </button></td>
              <td><StatusChip state={doc.state}/></td>
              <td className="muted-cell">{shortDate(doc.created_at)}</td>
              <td className="muted-cell">{bytes(doc.size_bytes)}</td>
              <td className="end-cell"><button aria-label={`Ouvrir ${doc.original_name}`} className="icon-button" type="button" onClick={() => onSelect(doc)}><ChevronRight size={18}/></button></td>
            </tr>)}
          </tbody>
        </table>
      </div>
      {!displayed.length && <EmptyState title={loading ? "Chargement en cours" : "Aucun document correspondant"}
        description={loading ? "Lecture des données réelles…" : "Modifie le filtre ou la recherche pour afficher les documents."}/>}
      <div className="table-bottom">
        <span>Filtre local sur la page · {displayed.length} résultat(s) affiché(s)</span>
        <div className="pager">
          <button type="button" disabled={page <= 1 || loading} onClick={() => onPage(page - 1)} aria-label="Page précédente"><ArrowLeft size={16}/></button>
          <strong>Page {page}</strong>
          <button type="button" disabled={!listing?.next || loading} onClick={() => onPage(page + 1)} aria-label="Page suivante"><ArrowRight size={16}/></button>
        </div>
      </div>
    </Pane>
    <Hint>La planification Airflow, la consommation de fichiers et la génération de réponses IA sont trois opérations différentes. L'import seul ne crée pas de facture validée.</Hint>
    {selected && <DocumentDrawer doc={selected} detail={detail} busy={actionBusy}
      loading={detailLoading} demo={demo} operator={operator} aiEnabled={aiEnabled}
      onClose={() => onSelect(null)} onProcess={onProcess} onIndex={onIndex}/>}
  </div>;
}

function DocumentDrawer({
  doc, detail, loading, demo, operator, aiEnabled, busy, onClose, onProcess, onIndex,
}: {
  doc: Document; detail: DocumentDetail | null; loading: boolean;
  demo: boolean; operator: boolean; aiEnabled: boolean; busy: string | null;
  onClose: () => void; onProcess: (doc: Document, force?: boolean) => Promise<void>;
  onIndex: (doc: Document) => Promise<void>;
}) {
  const [section, setSection] = useState<"invoices" | "records" | "issues" | "history">("invoices");
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    closeRef.current?.focus();
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, [onClose]);
  const actionAllowed = operator && !demo && !busy;
  const canProcess = doc.state === "RECEIVED" || doc.state === "REJECTED";
  const canIndex = doc.state === "ACCEPTED" && aiEnabled;

  return <div className="drawer-layer">
    <button className="drawer-scrim" onClick={onClose} type="button" aria-label="Fermer les détails du document"/>
    <aside className="document-drawer glass" role="dialog" aria-modal="true" aria-label={`Détails de ${doc.original_name}`}>
      <div className="drawer-header">
        <div><div className="eyebrow">FICHE DOCUMENTAIRE</div><h2>{doc.original_name}</h2></div>
        <button ref={closeRef} type="button" className="icon-button" onClick={onClose} aria-label="Fermer"><X size={19}/></button>
      </div>
      <div className="drawer-scroll">
        <div className="detail-summary">
          <span className={`file-badge file-${doc.file_type.toLowerCase()}`}>{doc.file_type}</span>
          <StatusChip state={doc.state}/>
          {doc.source === "DEMO" && <LabelPill kind="info">Fictif</LabelPill>}
        </div>
        <div className="detail-grid">
          <Field label="Date d'import">{shortDate(doc.created_at)}</Field>
          <Field label="Taille">{bytes(doc.size_bytes)}</Field>
          <Field label="Type">{doc.file_type}</Field>
          <Field label="Statut">{stateLabels[doc.state]}</Field>
        </div>
        <div className="fingerprint"><Fingerprint size={16}/>
          <div><span>Empreinte SHA-256</span><code>{doc.sha256}</code></div></div>
        {demo ? <EmptyState icon="shield" title="Métadonnées fictives uniquement"
          description="Ce document n'a pas de fichier source, de facture calculée, d'extrait ni de trace d'IA sur Render."/> :
        <>
          <div className="drawer-actions">
            {operator && <button type="button" className="btn btn-secondary" disabled={!actionAllowed || !canProcess}
              onClick={() => void onProcess(doc, doc.state === "REJECTED")}>
              <FileCheck size={16}/>{doc.state === "REJECTED" ? "Retraiter" : "Traiter avec D2"}
            </button>}
            {operator && <button type="button" className="btn btn-primary" disabled={!actionAllowed || !canIndex}
              onClick={() => void onIndex(doc)}><Sparkles size={15}/>Indexer pour l'IA</button>}
          </div>
          {!operator && <Hint>Ton compte peut consulter les documents, mais le traitement et l'indexation nécessitent le rôle opérateur.</Hint>}
          {!aiEnabled && <Hint>L'index IA nécessite l'instance locale Ollama/Chroma. Les données ne sont pas envoyées à un service externe.</Hint>}
          <div className="detail-tabs" role="tablist" aria-label="Informations du document">
            {([["invoices","Factures"],["records","Extraits"],["issues","Anomalies"],["history","Historique"]] as const).map(([id,label]) =>
              <button type="button" role="tab" aria-selected={section === id} className={section === id ? "active" : ""}
                key={id} onClick={() => setSection(id)}>{label}</button>)}
          </div>
          {loading && <div className="drawer-placeholder">Chargement des informations…</div>}
          {!loading && detail && section === "invoices" &&
            (detail.invoices.length ? <div className="detail-list">{detail.invoices.map(inv => <article key={inv.id} className="detail-record">
              <div className="detail-record-title"><strong>{inv.invoice_number}</strong><LabelPill kind="good">Validée</LabelPill></div>
              <div className="record-line"><span>{inv.supplier_name}</span><span>{inv.issued_on}</span></div>
              <div className="record-line"><span>TTC {money(inv.total, inv.currency)}</span><span>HT {money(inv.subtotal, inv.currency)}</span></div>
              <small>Origine : {inv.source_locator}</small>
            </article>)}</div> :
            <EmptyState title="Aucune facture validée" description="Le traitement doit réussir avant que des montants alimentent les tableaux SQL."/>)}
          {!loading && detail && section === "records" &&
            (detail.records.length ? <div className="detail-list">{detail.records.map(r => <article className="detail-record" key={r.id}>
              <strong>{r.source_locator}</strong>
              <dl className="record-fields">{Object.entries(r.normalized_fields).map(([key, value]) =>
                <div key={key}><dt>{key}</dt><dd>{typeof value === "object" ? JSON.stringify(value) : String(value ?? "—")}</dd></div>)}</dl>
            </article>)}</div> : <EmptyState title="Aucun extrait" description="Le document n'a pas encore été traité, ou sa validation n'a fourni aucun extrait." />)}
          {!loading && detail && section === "issues" &&
            (detail.issues.length ? <div className="detail-list">{detail.issues.map(issue => <article className="detail-record issue-record" key={issue.id}>
              <span className="issue-title"><AlertTriangle size={15}/> {issue.code}</span>
              <p>{issue.message}</p><small>{issue.source_locator || "Document"} · Champ : {issue.field_name || "—"}</small>
            </article>)}</div> : <EmptyState title="Aucune anomalie enregistrée" description="Les règles de qualité n'ont produit aucun diagnostic sur ce document." />)}
          {!loading && detail && section === "history" &&
            <div className="detail-list">
              {detail.runs.map(run => <article className="detail-record" key={run.id}>
                <div className="detail-record-title"><strong>Traitement {run.pipeline_version}</strong><LabelPill kind={run.status === "SUCCEEDED" ? "good" : run.status === "REJECTED" ? "danger" : "info"}>{run.status}</LabelPill></div>
                <p>Tentative {run.attempt_number} · {shortDate(run.started_at)}</p>
                {run.error_summary && <small>{run.error_summary}</small>}
              </article>)}
              {detail.audit.map(entry => <article className="audit-entry" key={entry.id}>
                <CheckCircle2 size={15}/><div><strong>{entry.action}</strong>
                  <small>{shortDate(entry.created_at)} · {entry.actor ?? "Système"}</small></div>
              </article>)}
              {!detail.runs.length && !detail.audit.length && <EmptyState icon="chart" title="Aucun événement" description="L'historique apparaîtra lors des traitements."/>}
            </div>}
        </>}
      </div>
    </aside>
  </div>;
}
