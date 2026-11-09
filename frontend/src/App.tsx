import { useCallback, useEffect, useRef, useState } from "react";
import {
  Activity, ArrowRight, BarChart3, BrainCircuit,
  Check, ChevronRight, CircleAlert, Database,
  Files, Fingerprint, LayoutDashboard, LockKeyhole, LogOut,
  Menu, RefreshCcw, ShieldCheck, X,
} from "lucide-react";
import { api } from "./api";
import type {
  Analytics, AssistantAnswer, AssistantStatus, Audit, Document,
  DocumentDetail, Overview, Page, Session, Tab,
} from "./types";
import OverviewView from "./pages/Overview";
import { DocumentsView } from "./pages/Documents";
import AnalyticsView from "./pages/Analytics";
import AssistantView from "./pages/Assistant";
import ActivityView from "./pages/Activity";

const navigation = [
  { id: "overview" as Tab, label: "Vue d'ensemble", icon: LayoutDashboard },
  { id: "documents" as Tab, label: "Documents", icon: Files },
  { id: "analytics" as Tab, label: "Analyse & KPI", icon: BarChart3 },
  { id: "assistant" as Tab, label: "Assistant IA", icon: BrainCircuit },
  { id: "activity" as Tab, label: "Historique", icon: Activity },
];
const titles: Record<Tab, string> = {
  overview: "Vue d'ensemble",
  documents: "Documents",
  analytics: "Analyse & KPI",
  assistant: "Assistant IA",
  activity: "Historique",
};

const emptyDetail: DocumentDetail = {
  invoices: [], records: [], issues: [], runs: [], audit: [],
};

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Une erreur imprévue est survenue.";
}

function LoginScreen({
  onLogin, busy, error,
}: { onLogin: (username: string, password: string) => Promise<void>; busy: boolean; error: string | null }) {
  const [username, setUsername] = useState("documind-local");
  const [password, setPassword] = useState("");
  return <div className="login-screen">
    <div className="login-aura" aria-hidden="true"/>
    <div className="login-card glass">
      <div className="login-brand"><span className="brand-symbol"><Fingerprint size={29}/></span>
        <strong>DOCUMIND<span>.</span></strong></div>
      <div className="eyebrow">LOCAL / ESPACE PRIVÉ</div>
      <h1>Bienvenue dans<br/><span>votre workspace.</span></h1>
      <p>Connectez-vous avec l'identifiant local créé par la recette D5. Aucun compte cloud n'est nécessaire.</p>
      <form onSubmit={event => { event.preventDefault(); void onLogin(username, password); }}>
        <label htmlFor="login-username">Identifiant</label>
        <input id="login-username" value={username} onChange={event => setUsername(event.target.value)}
          autoComplete="username" required maxLength={150}/>
        <label htmlFor="login-password">Mot de passe local</label>
        <input id="login-password" type="password" value={password}
          onChange={event => setPassword(event.target.value)}
          autoComplete="current-password" required/>
        {error && <div className="inline-error" role="alert"><CircleAlert size={15}/>{error}</div>}
        <button className="btn btn-primary login-submit" disabled={busy || !password || !username} type="submit">
          <LockKeyhole size={17}/>{busy ? "Authentification…" : "Accéder à DocuMind"}<ArrowRight size={15}/>
        </button>
      </form>
      <div className="login-foot"><ShieldCheck size={16}/> Session Django sécurisée · CSRF actif · Données locales</div>
      <small>Les identifiants sont conservés uniquement dans le dossier privé local de l'installation.</small>
    </div>
    <div className="login-aside"><div className="login-number">01 / 05</div><p>Une intelligence documentaire<br/><strong>traçable de bout en bout.</strong></p></div>
  </div>;
}

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);
  const [view, setView] = useState<Tab>("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [docs, setDocs] = useState<Page<Document> | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [audits, setAudits] = useState<{count:number;results:Audit[]}>({count:0,results:[]});
  const [assistantStatus, setAssistantStatus] = useState<AssistantStatus | null>(null);
  const [selected, setSelected] = useState<Document | null>(null);
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [refreshKey, setRefreshKey] = useState(0);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  const demo = session?.mode === "synthetic-demo";
  const canLoad = Boolean(session && (demo || session.authenticated));
  const aiEnabled = Boolean(session?.ai_enabled && !demo);
  const operator = Boolean(session?.operator && !demo);

  useEffect(() => {
    let alive = true;
    api.session().then(result => {if (alive) setSession(result);})
      .catch(err => {if (alive) setBootError(errorMessage(err));});
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (!canLoad) return;
    let active = true;
    setLoading(true);
    async function update() {
      const [ov, list, bi, audit] = await Promise.allSettled([
        api.overview(), api.documents(page), api.analytics(), api.audit(),
      ]);
      if (!active) return;
      if (ov.status === "fulfilled") setOverview(ov.value);
      if (list.status === "fulfilled") setDocs(list.value);
      if (bi.status === "fulfilled") setAnalytics(bi.value);
      if (audit.status === "fulfilled") setAudits(audit.value);
      const failures = [ov, list, bi, audit].filter(item => item.status === "rejected");
      if (failures.length) {
        setError(`${failures.length} source(s) n'ont pas pu être chargées. Certaines zones peuvent être indisponibles.`);
      }
      setLoading(false);
    }
    void update();
    return () => { active = false; };
  }, [canLoad, page, refreshKey, session]);

  useEffect(() => {
    if (!canLoad || !selected || demo) {setDetail(null);setDetailLoading(false);return;}
    let alive = true;
    setDetailLoading(true);
    const id = selected.id;
    Promise.all([
      api.invoices(id), api.records(id), api.issues(id), api.runs(id), api.audit(id),
    ]).then(([invoices, records, issues, runs, history]) => {
      if (alive) setDetail({
        invoices: invoices.results, records: records.results,
        issues: issues.results, runs: runs.results, audit: history.results,
      });
    }).catch(err => {if (alive) {setError(errorMessage(err));setDetail(emptyDetail);}})
      .finally(() => {if (alive) setDetailLoading(false);});
    return () => {alive = false;};
  }, [selected?.id, refreshKey, canLoad, demo, session]);

  useEffect(() => {
    if (!aiEnabled) {setAssistantStatus(null);return;}
    let alive = true;
    api.assistantStatus().then(status => {if(alive) setAssistantStatus(status);})
      .catch(() => {if(alive) setAssistantStatus(null);});
    return () => {alive = false;};
  }, [aiEnabled, refreshKey, session]);

  const refresh = () => setRefreshKey(key => key + 1);
  const navigate = (target: Tab) => {
    setView(target);
    setSidebarOpen(false);
    mainRef.current?.scrollTo({top:0,behavior:"smooth"});
  };
  const openDocument = useCallback((doc: Document) => {
    setSelected(doc);
    setView("documents");
    setSidebarOpen(false);
  }, []);
  const openDocumentId = async (id: string) => {
    if (demo) return;
    try { openDocument(await api.document(id)); }
    catch (err) {setError(errorMessage(err));}
  };

  const doLogin = async (username: string, password: string) => {
    if (!session) return;
    setBusy("login");setError(null);
    try {
      await api.login(username, password, session.csrf_token);
      const current = await api.session();
      setSession(current);
      setPage(1);
      setNotice("Session locale ouverte.");
    } catch (err) {setError(errorMessage(err));}
    finally {setBusy(null);}
  };
  const doLogout = async () => {
    if (!session) return;
    setBusy("logout");setError(null);
    try {
      await api.logout(session.csrf_token);
      setOverview(null);setDocs(null);setAnalytics(null);setSelected(null);
      setAudits({count:0,results:[]});
      setSession(await api.session());
      navigate("overview");
      setNotice("Session locale fermée.");
    } catch (err) {setError(errorMessage(err));}
    finally {setBusy(null);}
  };

  const upload = async (file: File) => {
    if (!session || !operator) throw new Error("Import non autorisé.");
    setBusy("upload");setError(null);
    try {
      const document = await api.upload(file, session.csrf_token);
      setNotice(`Document « ${document.original_name} » reçu. Il reste à le traiter.`);
      setPage(1);refresh();
    } catch (err) {throw new Error(errorMessage(err));}
    finally {setBusy(null);}
  };
  const process = async (doc: Document, force = false) => {
    if (!session || !operator) return;
    setBusy(doc.id);setError(null);
    try {
      const result = await api.process(doc.id, session.csrf_token, force);
      setNotice(result.status === "SUCCEEDED"
        ? `Traitement terminé : ${result.invoices_count} facture(s) validée(s).`
        : `Traitement ${result.status} : consulte les anomalies.`);
      setSelected(await api.document(doc.id));
      refresh();
    } catch (err) {setError(errorMessage(err));}
    finally {setBusy(null);}
  };
  const index = async (doc: Document) => {
    if (!session || !operator || !aiEnabled) return;
    setBusy(doc.id);setError(null);
    try {
      const result = await api.index(doc.id, session.csrf_token);
      setNotice(result.skipped ? "Document déjà indexé, sans doublon."
        : `${result.indexed_chunks} passage(s) indexé(s) avec provenance.`);
      setSelected(await api.document(doc.id));
      refresh();
    } catch (err) {setError(errorMessage(err));}
    finally {setBusy(null);}
  };
  const ask = async (question: string): Promise<AssistantAnswer> => {
    if (!session || !aiEnabled) throw new Error("Assistant IA local désactivé.");
    return api.ask(question, session.csrf_token);
  };

  if (bootError && !session) return <div className="fatal-screen">
    <div className="glass fatal-panel"><CircleAlert size={30}/>
      <h1>Connexion au service impossible</h1><p>{bootError}</p>
      <button className="btn btn-primary" type="button" onClick={() => window.location.reload()}>
        <RefreshCcw size={16}/> Réessayer
      </button></div>
  </div>;
  if (!session) return <div className="splash-screen" role="status">
    <span className="brand-symbol"><Fingerprint size={30}/></span><strong>DOCUMIND<span>.</span></strong>
    <p>Initialisation de l'espace documentaire…</p>
  </div>;
  if (!demo && !session.authenticated) return <LoginScreen
    onLogin={doLogin} busy={busy === "login"} error={error}/>;

  return <div className="app-shell">
    {sidebarOpen && <button className="mobile-scrim" type="button"
      aria-label="Fermer la navigation" onClick={() => setSidebarOpen(false)}/>}
    <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`} aria-label="Navigation principale">
      <div className="sidebar-brand">
        <span className="brand-symbol"><Fingerprint size={25} strokeWidth={1.7}/></span>
        <div><strong>DOCUMIND<span>.</span></strong><small>INTELLIGENT WORKSPACE</small></div>
        <button className="sidebar-close" type="button" onClick={() => setSidebarOpen(false)}
          aria-label="Fermer la navigation"><X size={19}/></button>
      </div>
      <div className="sidebar-label">ESPACE DE TRAVAIL</div>
      <nav className="sidebar-nav" aria-label="Sections de DocuMind">
        {navigation.map(item => {
          const Icon = item.icon;
          return <button key={item.id} type="button" aria-current={view === item.id ? "page" : undefined}
            className={`nav-item ${view === item.id ? "active" : ""}`}
            onClick={() => navigate(item.id)}>
            <Icon size={19} strokeWidth={1.9}/><span>{item.label}</span>
            {view === item.id && <ChevronRight size={15} className="nav-arrow"/>}
          </button>;
        })}
      </nav>
      <div className="sidebar-label sidebar-tools-label">ENVIRONNEMENT</div>
      <div className="sidebar-env">
        <div><span className="env-icon"><Database size={17}/></span>
          <p><strong>{demo ? "Render Free" : "PostgreSQL local"}</strong>
            <small>{demo ? "Métadonnées fictives" : "Source de vérité"}</small></p></div>
        <div><span className="env-icon"><BrainCircuit size={17}/></span>
          <p><strong>Assistant D4</strong>
            <small>{aiEnabled ? "Ollama local actif" : "Non disponible"}</small></p></div>
        <div><span className="env-icon"><ShieldCheck size={17}/></span>
          <p><strong>Intégrité</strong><small>Provenance & audit</small></p></div>
      </div>
      <div className="sidebar-spacer"/>
      <div className="sidebar-status glass">
        <span className="sidebar-status-top"><span className="signal-pulse"/>{demo ? "DÉMO PUBLIQUE" : "SESSION LOCALE"}</span>
        <strong>{demo ? "Lecture seule" : operator ? "Opérateur" : "Consultation"}</strong>
        <small>{demo ? "Aucun traitement simulé." : "Données hébergées localement."}</small>
      </div>
      <div className="sidebar-footer"><span>DocuMind V1.0</span><span className="version-dot"/></div>
    </aside>

    <div className="workspace">
      <header className="topbar">
        <div className="topbar-left">
          <button className="mobile-menu icon-button" type="button" aria-label="Ouvrir la navigation"
            onClick={() => setSidebarOpen(true)}><Menu size={21}/></button>
          <div className="breadcrumbs"><span>Workspace</span><ChevronRight size={14}/><strong>{titles[view]}</strong></div>
        </div>
        <div className="topbar-right">
          <span className={`topbar-mode ${demo ? "demo" : ""}`}><span className="signal-pulse"/>
            {demo ? "Démonstration" : "Instance locale"}</span>
          <button className="icon-button" type="button" disabled={loading}
            onClick={refresh} aria-label="Actualiser les données" title="Actualiser">
            <RefreshCcw size={18} className={loading ? "spinning" : ""}/>
          </button>
          <span className="topbar-divider"/>
          <span className="user-circle" aria-label={demo ? "Visiteur" : session.username ?? "Utilisateur"}>
            {demo ? "DM" : (session.username ?? "U").slice(0, 2).toUpperCase()}
          </span>
          {!demo && <button type="button" className="icon-button logout-button"
            disabled={busy === "logout"} onClick={() => void doLogout()} aria-label="Se déconnecter" title="Se déconnecter">
            <LogOut size={17}/></button>}
        </div>
      </header>

      <main ref={mainRef} className="workspace-content" id="main-content">
        {view === "overview" && <OverviewView overview={overview} analytics={analytics}
          documents={docs?.results ?? []} demo={Boolean(demo)} loading={loading}
          onTab={navigate} onDocument={openDocument}/>}
        {view === "documents" && <DocumentsView listing={docs} loading={loading}
          selected={selected} detail={detail} detailLoading={detailLoading}
          demo={Boolean(demo)} operator={operator} aiEnabled={aiEnabled}
          actionBusy={busy} page={page} onPage={setPage} onSelect={setSelected}
          onUpload={upload} onProcess={process} onIndex={index}/>}
        {view === "analytics" && <AnalyticsView data={analytics} overview={overview}
          demo={Boolean(demo)}/>}
        {view === "assistant" && <AssistantView demo={Boolean(demo)} enabled={aiEnabled}
          status={assistantStatus} onAsk={ask}
          onCitation={id => void openDocumentId(id)}/>}
        {view === "activity" && <ActivityView events={audits.results} count={audits.count}
          demo={Boolean(demo)} onDocument={id => void openDocumentId(id)}/>}
        <footer className="workspace-footer">
          <span><ShieldCheck size={14}/> Aucun chiffre non vérifié · Données fictives identifiées</span>
          <span>Django · PostgreSQL · Pandas · Metabase · Ollama</span>
        </footer>
      </main>
      {error && <div role="alert" className="toast toast-error">
        <CircleAlert size={18}/><span>{error}</span><button type="button"
          aria-label="Fermer l'erreur" onClick={() => setError(null)}><X size={16}/></button>
      </div>}
      {notice && <div role="status" className="toast toast-success">
        <Check size={18}/><span>{notice}</span><button type="button"
          aria-label="Fermer la notification" onClick={() => setNotice(null)}><X size={16}/></button>
      </div>}
    </div>
  </div>;
}
