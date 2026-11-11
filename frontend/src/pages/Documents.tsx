import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle, ArrowLeft, ArrowRight, CheckCircle2, ChevronRight,
  CloudUpload, FileCheck, FileClock, FileText, FileUp, Fingerprint, LockKeyhole,
  Search, ShieldCheck, Sparkles, Upload, X,
} from "lucide-react";
import type { Document, Overview, Page } from "../types";
import type { DocumentDetail } from "../types";
import { bytes, money, shortDate, stateLabels } from "../format";
import { displayFieldValue, eventDate, eventLabel, eventTone, fieldLabel, issueLabel, mismatchEvidence, runLabel, sourceLabel } from "../ux";
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
  overview: Overview | null;
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
  listing, overview, loading, selected, detail, detailLoading, demo, operator,
  aiEnabled, actionBusy, page, onPage, onSelect, onUpload, onProcess, onIndex,
}: Props) {
  const [filter, setFilter] = useState<(typeof filters)[number]["id"]>("all");
  const [search, setSearch] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const ref = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [desktop, setDesktop] = useState(() =>
    typeof window === "undefined" || window.matchMedia("(min-width: 1120px)").matches,
  );
  const pickedInitial = useRef(false);
  useEffect(() => {
    const query = window.matchMedia("(min-width: 1120px)");
    const sync = () => setDesktop(query.matches);
    query.addEventListener("change", sync);
    return () => query.removeEventListener("change", sync);
  }, []);
  useEffect(() => {
    if (!desktop || pickedInitial.current || selected || loading || !listing?.results.length) return;
    pickedInitial.current = true;
    onSelect(listing.results[0]);
  }, [desktop, selected, loading, listing, onSelect]);
  const closePreview = useCallback(() => onSelect(null), [onSelect]);
  const chooseFile = (next: File | null) => { setFile(next); setFileError(null); };
  const totalDocuments = overview?.total ?? listing?.count ?? null;
  const validDocuments = overview?.processed ?? null;
  const rejectedDocuments = overview?.rejected ?? null;
  const waitingDocuments = overview
    ? Math.max(0, overview.total - overview.processed - overview.rejected) : null;
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

  return <div className="page-stack documents-page documents-premium-page">
    <header className="documents-hero glass">
      <div className="documents-hero-glow" aria-hidden="true"/>
      <div className="documents-hero-main">
        <div className="documents-hero-content">
          <div className="eyebrow"><span className="signal-pulse"/> DOCUMENTS / CATALOGUE</div>
          <h1>Bibliothèque <span>documentaire</span></h1>
          <p>Centralisez vos fichiers, contrôlez leur cohérence, puis retrouvez chaque donnée et sa provenance.</p>
          <div className="documents-hero-actions">
            <button className="btn btn-primary" type="button" disabled={!canUpload}
              onClick={() => ref.current?.click()}>
              <Upload size={17}/> Importer un document <ArrowRight size={16}/>
            </button>
            <span className="documents-hero-context">
              <ShieldCheck size={15}/>
              {demo ? "Démonstration en lecture seule" : operator ? "Import et contrôles locaux" : "Consultation uniquement"}
            </span>
          </div>
        </div>
        <div className="documents-hero-illustration" aria-hidden="true">
          <div className="documents-hero-arc"/>
          <div className="documents-hero-illustration-doc ghost"/>
          <div className="documents-hero-illustration-doc middle"/>
          <div className="documents-hero-illustration-doc front">
            <Fingerprint size={32}/><i/><i/><i/>
            <span className="documents-hero-check"><FileCheck size={24}/></span>
          </div>
          <span className="documents-hero-floating one"><FileText size={19}/></span>
          <span className="documents-hero-floating two"><ShieldCheck size={19}/></span>
        </div>
      </div>
      <div className="documents-hero-bottom">
        <div className={dragOver ? "documents-upload-box is-dragging" : "documents-upload-box"}
          onDragOver={event => { event.preventDefault(); if (canUpload) setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={event => {
            event.preventDefault();
            setDragOver(false);
            if (canUpload) chooseFile(event.dataTransfer.files?.[0] ?? null);
          }}>
          <button type="button" className="documents-dropzone" disabled={!canUpload}
            onClick={() => ref.current?.click()}>
            <CloudUpload size={24}/>
            <span><strong>{file ? file.name : "Déposez votre fichier ici"}</strong>
              <small>PDF textuel, CSV ou XLSX · 5 Mio maximum</small></span>
          </button>
          <input ref={ref} id="doc-upload" className="sr-only" type="file"
            accept=".pdf,.csv,.xlsx" aria-label="Choisir un document à importer"
            disabled={!canUpload} onChange={event => chooseFile(event.target.files?.[0] ?? null)}/>
          <span className="documents-upload-or">ou</span>
          <button type="button" className="documents-upload-picker btn btn-secondary"
            disabled={!canUpload} onClick={() => ref.current?.click()}>
            <FileUp size={16}/> Choisir un fichier
          </button>
          <button type="button" className="documents-upload-submit btn btn-primary"
            disabled={!file || !canUpload || Boolean(actionBusy)} onClick={() => void upload()}>
            {actionBusy === "upload" ? "Import en cours…" : "Importer"}
          </button>
        </div>
        <div className="documents-overview-stats" aria-label="États réels des documents">
          <div className="documents-overview-stat">
            <FileText size={20}/><span><strong>{totalDocuments ?? "—"}</strong><small>Documents</small></span>
          </div>
          <div className="documents-overview-stat is-valid">
            <FileCheck size={20}/><span><strong>{validDocuments ?? "—"}</strong><small>Validés / indexés</small></span>
          </div>
          <div className="documents-overview-stat is-waiting">
            <FileClock size={20}/><span><strong>{waitingDocuments ?? "—"}</strong><small>En attente</small></span>
          </div>
          <div className="documents-overview-stat is-rejected">
            <AlertTriangle size={20}/><span><strong>{rejectedDocuments ?? "—"}</strong><small>Rejetés</small></span>
          </div>
        </div>
      </div>
      {fileError && <div className="inline-error documents-import-error" role="alert">{fileError}</div>}
    </header>

    <div className="documents-cockpit">
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
            {displayed.map(doc => <tr key={doc.id} className={selected?.id === doc.id ? "is-current" : ""}>
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
      {!displayed.length && <EmptyState
        title={loading ? "Chargement en cours" : (listing?.count ?? 0) === 0 ? "Aucun document importé" : "Aucun document correspondant"}
        description={loading ? "Lecture des données…" :
          (listing?.count ?? 0) === 0 ? "Importez votre premier fichier depuis le panneau supérieur." :
            "Modifiez le filtre ou la recherche pour afficher les documents de cette page."}/>}
      <div className="table-bottom">
        <span>Filtre local sur la page · {displayed.length} résultat(s) affiché(s)</span>
        <div className="pager">
          <button type="button" disabled={page <= 1 || loading} onClick={() => onPage(page - 1)} aria-label="Page précédente"><ArrowLeft size={16}/></button>
          <strong>Page {page}</strong>
          <button type="button" disabled={!listing?.next || loading} onClick={() => onPage(page + 1)} aria-label="Page suivante"><ArrowRight size={16}/></button>
        </div>
      </div>
    </Pane>
      {selected ? <DocumentDrawer doc={selected} detail={detail} busy={actionBusy}
        loading={detailLoading} demo={demo} operator={operator} aiEnabled={aiEnabled}
        desktop={desktop} onClose={closePreview} onProcess={onProcess} onIndex={onIndex}/> :
        <section className="documents-preview-empty glass" aria-label="Fiche documentaire">
          <div className="documents-preview-empty-icon"><FileText size={29}/></div>
          <h2>Fiche documentaire</h2>
          <p>Sélectionnez un document dans le catalogue pour consulter sa provenance, ses extractions, ses éventuelles anomalies et son historique.</p>
          <span><ShieldCheck size={16}/> Sources et opérations vérifiables</span>
        </section>}
    </div>
    <Hint>Importer, traiter avec D2 et indexer pour l'IA sont trois opérations distinctes. Les documents rejetés ne contribuent pas aux indicateurs validés.</Hint>
  </div>;
}

function DocumentDrawer({
  doc, detail, loading, demo, operator, aiEnabled, busy, desktop, onClose, onProcess, onIndex,
}: {
  doc: Document; detail: DocumentDetail | null; loading: boolean;
  demo: boolean; operator: boolean; aiEnabled: boolean; busy: string | null; desktop: boolean;
  onClose: () => void; onProcess: (doc: Document, force?: boolean) => Promise<void>;
  onIndex: (doc: Document) => Promise<void>;
}) {
  const [section, setSection] = useState<"overview" | "invoices" | "records" | "issues" | "history">("overview");
  useEffect(() => setSection("overview"), [doc.id]);
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!desktop) closeRef.current?.focus();
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, [onClose, desktop]);
  const actionAllowed = operator && !demo && !busy;
  const canProcess = doc.state === "RECEIVED" || doc.state === "REJECTED";
  const canIndex = doc.state === "ACCEPTED" && aiEnabled;

  return <div className="drawer-layer documents-preview-layer">
    <button className="drawer-scrim" onClick={onClose} type="button" aria-label="Fermer les détails du document"/>
    <aside className="document-drawer glass" role="dialog" aria-modal={!desktop} aria-label={`Détails de ${doc.original_name}`}>
      <div className="drawer-header">
        <div><div className="eyebrow">FICHE DOCUMENTAIRE</div><h2>{doc.original_name}</h2></div>
        <button ref={closeRef} type="button" className="icon-button" onClick={onClose} aria-label="Fermer"><X size={19}/></button>
      </div>
      <div className="drawer-scroll">
        {demo ? <EmptyState icon="shield" title="Métadonnées fictives uniquement"
          description="Ce document n'a pas de fichier source, de facture calculée, d'extrait ni de trace d'IA sur Render."/> :
        <>
          <div className="drawer-actions">
            {operator && canProcess && <button type="button" className="btn btn-secondary" disabled={!actionAllowed}
              onClick={() => void onProcess(doc, doc.state === "REJECTED")}>
              <FileCheck size={16}/>{doc.state === "REJECTED" ? "Retraiter le document" : "Traiter avec D2"}
            </button>}
            {operator && canIndex && <button type="button" className="btn btn-primary" disabled={!actionAllowed}
              onClick={() => void onIndex(doc)}><Sparkles size={15}/>Indexer pour l'IA</button>}
            {doc.state === "INDEXED" && <span className="already-indexed"><CheckCircle2 size={16}/> Déjà indexé</span>}
          </div>
          {doc.state === "REJECTED" && <Hint warning>Ce fichier a été rejeté. Le retraiter sans modifier sa source risque de reproduire le même rejet. Un document rejeté ne peut pas être indexé.</Hint>}
          {!operator && <Hint>Ton compte peut consulter les documents, mais le traitement et l'indexation nécessitent le rôle opérateur.</Hint>}
          {!aiEnabled && <Hint>L'index IA nécessite l'instance locale Ollama/Chroma. Les données ne sont pas envoyées à un service externe.</Hint>}
          <div className="detail-tabs" role="tablist" aria-label="Informations du document">
            {([["overview","Aperçu"],["invoices","Factures"],["records","Extraits"],["issues","Anomalies"],["history","Historique"]] as const).map(([id,label]) =>
              <button type="button" role="tab" aria-selected={section === id} className={section === id ? "active" : ""}
                key={id} onClick={() => setSection(id)}>{label}</button>)}
          </div>
          {section === "overview" && <div className="document-detail-overview">
            <div className="document-preview-metrics">
              <div className="document-preview-metric">
                <FileText size={20}/><span><strong>{loading ? "—" : detail?.records.length ?? "—"}</strong><small>Extraits disponibles</small></span>
              </div>
              <div className="document-preview-metric is-alert">
                <AlertTriangle size={20}/><span><strong>{loading ? "—" : detail?.issues.length ?? "—"}</strong><small>Anomalies détectées</small></span>
              </div>
            </div>
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
            {doc.state === "REJECTED" && <Hint warning>Les données extraites de ce document rejeté ne contribuent pas aux indicateurs financiers.</Hint>}
          </div>}
          {loading && <div className="drawer-placeholder">Chargement des informations…</div>}
          {!loading && detail && section === "invoices" &&
            (detail.invoices.length ? <div className="detail-list">{detail.invoices.map(inv => <article key={inv.id} className="detail-record">
              <div className="detail-record-title"><strong>{inv.invoice_number}</strong><LabelPill kind="good">Validée</LabelPill></div>
              <div className="record-line"><span>{inv.supplier_name}</span><span>{shortDate(inv.issued_on)}</span></div>
              <div className="record-line"><span>TTC {money(inv.total, inv.currency)}</span><span>HT {money(inv.subtotal, inv.currency)}</span></div>
              <small title={inv.source_locator}>Origine : {sourceLabel(inv.source_locator)}</small>
            </article>)}</div> :
            <EmptyState title="Aucune facture validée" description="Le traitement doit réussir avant que des montants alimentent les tableaux SQL."/>)}
          {!loading && detail && section === "records" &&
            (detail.records.length ? <div className="detail-list">
              {doc.state === "REJECTED" && <Hint warning>Données extraites non validées. Ces valeurs ne sont pas intégrées aux indicateurs financiers.</Hint>}
              {detail.records.map(r => <article className="detail-record" key={r.id}>
                <strong className="source-heading" title={r.source_locator}>{sourceLabel(r.source_locator)}</strong>
                <dl className="record-fields">{Object.entries(r.normalized_fields).map(([key, value]) =>
                  <div key={key}><dt title={key}>{fieldLabel(key)}</dt><dd>{displayFieldValue(key, value, r)}</dd></div>)}</dl>
              </article>)}</div> : <EmptyState title="Aucun extrait" description="Le document n'a pas encore été traité, ou sa validation n'a fourni aucun extrait." />)}
          {!loading && detail && section === "issues" &&
            (detail.issues.length ? <div className="detail-list">{detail.issues.map(issue => <article className="detail-record issue-record" key={issue.id}>
              <span className="issue-title"><AlertTriangle size={15}/> {issueLabel(issue.code)}</span>
              <p>{issue.message}</p>
              {issue.code === "TOTAL_MISMATCH" && (() => {
                const record = detail.records.find(r => r.id === issue.record || r.source_locator === issue.source_locator);
                const explanation = mismatchEvidence(record);
                return explanation ? <p className="issue-evidence">{explanation}</p> : null;
              })()}
              <small title={issue.source_locator}>{sourceLabel(issue.source_locator)} · Champ : {fieldLabel(issue.field_name || "—")} · Code : {issue.code}</small>
            </article>)}</div> : <EmptyState title="Aucune anomalie enregistrée" description="Les règles de qualité n'ont produit aucun diagnostic sur ce document." />)}
          {!loading && detail && section === "history" &&
            <div className="detail-list">
              {detail.runs.map(run => <article className="detail-record" key={run.id}>
                <div className="detail-record-title"><strong>Traitement {run.pipeline_version}</strong><LabelPill kind={run.status === "SUCCEEDED" ? "good" : run.status === "REJECTED" || run.status === "FAILED" ? "danger" : "info"}>{runLabel(run.status)}</LabelPill></div>
                <p>Tentative {run.attempt_number} · {eventDate(run.started_at)}</p>
                {run.error_summary && <small>{run.error_summary}</small>}
              </article>)}
              {detail.audit.map(entry => <article className={`audit-entry audit-${eventTone(entry.action)}`} key={entry.id}>
                {eventTone(entry.action) === "danger" ? <AlertTriangle size={15}/> : <CheckCircle2 size={15}/>}
                <div><strong title={entry.action}>{eventLabel(entry.action)}</strong>
                  <small>{eventDate(entry.created_at)} · {entry.actor ?? "Système"}</small></div>
              </article>)}
              {!detail.runs.length && !detail.audit.length && <EmptyState icon="chart" title="Aucun événement" description="L'historique apparaîtra lors des traitements."/>}
            </div>}
        </>}
      </div>
    </aside>
  </div>;
}
