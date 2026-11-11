import {
  Activity, ArrowRight, BrainCircuit, CheckCheck, FileCheck2,
  FileClock, FileWarning, Files, Fingerprint, GitBranch, LockKeyhole,
  ShieldCheck, Sparkles, TrendingUp,
} from "lucide-react";
import type { Analytics, Document, Overview, Tab } from "../types";
import { money, percent, shortDate, monthlyEUR } from "../format";
import { EmptyState, Hint, MonthlyChart, Pane, StatCard, StatusChip, StatusDonut, SupplierBars } from "../components/Visuals";

type Props = {
  overview: Overview | null;
  analytics: Analytics | null;
  documents: Document[];
  demo: boolean;
  loading: boolean;
  onTab: (tab: Tab) => void;
  onDocument: (document: Document) => void;
};

export default function OverviewView({
  overview, analytics, documents, demo, loading, onTab, onDocument,
}: Props) {
  const real = Boolean(analytics?.available);
  const eur = real ? analytics?.currencies.find(c => c.currency === "EUR") : null;
  const monthly = real ? monthlyEUR(analytics?.monthly ?? []) : [];
  const suppliers = real ? (analytics?.suppliers ?? []).filter(s => s.currency === "EUR") : [];
  const total = overview?.total ?? null;
  const accepted = overview?.processed ?? 0;
  const rejected = overview?.rejected ?? 0;
  const waiting = Math.max(0, (total ?? 0) - accepted - rejected);
  const rejectionRate = real ? percent(rejected, total ?? 0) : "—";

  return <div className="page-stack overview-view">
    <header className="welcome-hero overview-hero glass">
      <div className="hero-glow" aria-hidden="true"/>
      <div className="overview-hero-top">
        <div className="hero-content">
          <span className="eyebrow"><span className="signal-pulse"/> DOCUMIND / WORKSPACE V1.0</span>
          <h1>Gérez, vérifiez, analysez et interrogez <span>vos documents.</span></h1>
          <p>
            De l'import à l'analyse, chaque information est contrôlée, traçable
            et reliée à sa source. {demo
              ? "Cette démonstration publique présente uniquement des métadonnées fictives."
              : "Vos données restent sur votre infrastructure locale."}
          </p>
          <div className="hero-actions">
            <button className="btn btn-primary" onClick={() => onTab("documents")} type="button">
              <Files size={16}/>
              {total === 0 && !demo ? "Importer mon premier document" : "Explorer les documents"}
              <ArrowRight size={15}/>
            </button>
            <button className="btn btn-ghost" onClick={() => onTab("assistant")} type="button">
              <BrainCircuit size={16}/> Assistant IA
            </button>
          </div>
        </div>
        <div className="overview-hero-illustration" aria-hidden="true">
          <div className="overview-hero-wave"/>
          <div className="overview-hero-doc overview-hero-doc-back"><FileCheck2 size={26}/></div>
          <div className="overview-hero-doc overview-hero-doc-mid"><Files size={27}/></div>
          <div className="overview-hero-doc overview-hero-doc-front">
            <Fingerprint size={33}/>
            <span className="overview-hero-doc-lines"><i/><i/><i/></span>
            <span className="overview-hero-doc-check"><CheckCheck size={22}/></span>
          </div>
          <span className="overview-hero-floating overview-hero-floating-left"><ShieldCheck size={18}/></span>
          <span className="overview-hero-floating overview-hero-floating-right"><GitBranch size={18}/></span>
        </div>
      </div>
      <div className="overview-hero-kpis stat-grid" aria-label="Indicateurs documentaires">
        <StatCard label="Documents suivis" value={loading && total === null ? "—" : total ?? "—"}
          detail={demo ? "3 fiches de démonstration fictives" : "Documents présents dans PostgreSQL"}
          icon={<Files size={20}/>} accent/>
        <StatCard label="Validés ou indexés" value={overview?.processed ?? "—"}
          detail={demo ? "Traitement désactivé" : "Extraits contrôlés par D2"}
          icon={<CheckCheck size={20}/>}/>
        <StatCard label="Montant TTC vérifié" value={eur ? money(eur.total, "EUR") : "—"}
          detail={real ? "EUR · factures réellement acceptées" : "Aucun montant vérifié disponible"}
          icon={<TrendingUp size={20}/>}/>
        <StatCard label="Documents rejetés" value={overview?.rejected ?? "—"}
          detail={real ? `Taux de rejet : ${rejectionRate}` : "Aucune validation métier en démo"}
          icon={<FileWarning size={20}/>}/>
      </div>
    </header>

    <div className="overview-main-grid">
      <Pane title="Évolution des dépenses" className="overview-chart-pane" subtitle={real ? "Montants TTC · factures validées · EUR" : "Les analyses reposent uniquement sur les factures validées"}>
        {real ? <MonthlyChart rows={monthly}/> :
          <EmptyState icon="chart"
            title={demo ? "Analyse indisponible dans la démo" : loading ? "Chargement des analyses" : total === 0 ? "Aucune dépense validée" : "Analyses indisponibles"}
            description={demo ? "La démo publique ne calcule aucun montant financier."
              : loading ? "Récupération des vues SQL en cours."
                : total === 0 ? "Traitez des factures valides pour afficher les dépenses."
                  : "Les indicateurs SQL ne sont pas disponibles pour le moment."}/>}
      </Pane>
      <Pane title="Contrôle documentaire" className="overview-control-pane" subtitle="Répartition des états réels" aside={<Activity size={17} className="muted-icon"/>}>
        <StatusDonut accepted={accepted} received={waiting} rejected={rejected}/>
        <div className="subtle-divider"/>
        <div className="integrity-note"><LockKeyhole size={15}/>
          {demo ? "La démo ne traite aucun fichier." : "Les documents rejetés sont exclus des calculs."}
        </div>
      </Pane>
    </div>

    <div className="overview-lower-grid">
      <Pane title="Documents récents" className="overview-recent-pane" subtitle="Dernières entrées disponibles"
        aside={<button className="text-button" type="button" onClick={() => onTab("documents")}>Tout voir <ArrowRight size={14}/></button>}>
        {documents.length ? <div className="recent-docs">
          {documents.slice(0, 4).map(doc => <button key={doc.id} className="recent-doc" type="button" onClick={() => onDocument(doc)}>
            <span className={`file-badge file-${doc.file_type.toLowerCase()}`}>{doc.file_type}</span>
            <span className="recent-doc-main"><strong title={doc.original_name}>{doc.original_name}</strong>
              <small>{shortDate(doc.created_at)} · {doc.source === "DEMO" ? "Exemple fictif" : "Dépôt local"}</small></span>
            <StatusChip state={doc.state}/>
          </button>)}
        </div> : <EmptyState title="Aucun document" description={demo
            ? "Aucun fichier à afficher dans cet aperçu."
            : "Commencez dans Documents : importez un fichier, puis traitez-le pour vérifier ses données."}/>}
      </Pane>
      <Pane title="Principaux fournisseurs" className="overview-suppliers-pane" subtitle={real ? "Montants TTC vérifiés · EUR" : "Source : vues SQL D3"}
        aside={<button type="button" className="text-button" onClick={() => onTab("analytics")}>Analyse <ArrowRight size={14}/></button>}>
        {real ? <SupplierBars rows={suppliers}/> :
          <EmptyState icon="chart"
            title={demo ? "Analyse indisponible dans la démo" : loading ? "Chargement des fournisseurs" : total === 0 ? "Aucun fournisseur à afficher" : "Fournisseurs indisponibles"}
            description={demo ? "La démo publique ne contient pas de factures validées."
              : loading ? "Lecture des données financières en cours."
                : total === 0 ? "Les fournisseurs apparaîtront après validation de factures en EUR."
                  : "Les données fournisseurs ne sont pas disponibles pour le moment."}/>}
      </Pane>
      <Pane title="Intégrité & provenance" className="overview-integrity-pane" subtitle="Le circuit de confiance DocuMind">
        <div className="trust-steps">
          <div><span><FileClock size={17}/></span><p><strong>01 · Réception</strong><small>Fichier et empreinte SHA-256</small></p></div>
          <div><span><FileCheck2 size={17}/></span><p><strong>02 · Validation</strong><small>Contrôles et anomalies D2</small></p></div>
          <div><span><Sparkles size={17}/></span><p><strong>03 · Citation</strong><small>Passages vérifiés par D4</small></p></div>
        </div>
        <Hint>{demo
          ? "Le parcours ci-dessus décrit le fonctionnement local. Il n'est pas exécuté sur la démonstration publique."
          : "Chaque facture et citation peut être reliée à son document et à sa ligne ou page source."}</Hint>
      </Pane>
    </div>
  </div>;
}
