import {
  ArrowUpRight, BadgeCheck, BarChart3, CircleHelp, FileCheck2,
  FileX2,
} from "lucide-react";
import type { Analytics, Overview } from "../types";
import { money, monthlyEUR, percent } from "../format";
import { EmptyState, Hint, MonthlyChart, Pane, StatCard, StatusDonut, SupplierBars } from "../components/Visuals";
import { issueLabel } from "../ux";

export default function AnalyticsView({
  data, overview, demo,
}: { data: Analytics | null; overview: Overview | null; demo: boolean }) {
  const ready = Boolean(data?.available);
  const eur = data?.currencies.find(item => item.currency === "EUR");
  const monthly = monthlyEUR(data?.monthly ?? []);
  const suppliers = (data?.suppliers ?? []).filter(row => row.currency === "EUR");
  const rejected = overview?.rejected ?? 0;
  const total = overview?.total ?? 0;

  return <div className="page-stack analytics-page analytics-premium-page">
    <section className="analytics-premium-hero glass" aria-label="Intelligence analytique et indicateurs">
      <div className="analytics-hero-top">
        <div className="analytics-hero-copy">
          <div className="eyebrow"><span className="signal-pulse"/> ANALYSE / POSTGRESQL D3</div>
          <h1>Intelligence <span>analytique</span></h1>
          <p>Des indicateurs calculés en SQL, sans montant inventé ni addition de devises.</p>
        </div>
        {!demo && <a className="btn btn-secondary analytics-metabase-link" href="http://127.0.0.1:3033"
          target="_blank" rel="noreferrer"><BarChart3 size={16}/> Ouvrir Metabase <ArrowUpRight size={15}/></a>}
        <div className="analytics-hero-illustration" aria-hidden="true">
          <span className="analytics-hero-wave"/>
          <div className="analytics-hero-chart analytics-hero-chart-back"/>
          <div className="analytics-hero-chart analytics-hero-chart-mid"/>
          <div className="analytics-hero-chart analytics-hero-chart-front">
            <span className="analytics-hero-bars"><i/><i/><i/><i/></span>
          </div>
        </div>
      </div>
      {ready && <div className="stat-grid analytics-premium-kpis">
        <StatCard label="Factures acceptées" value={data!.currencies.reduce((sum, c) => sum + c.invoice_count, 0)}
          icon={<FileCheck2 size={20}/>} detail="Toutes devises · nombre de factures" accent/>
        <StatCard label="Montant TTC · EUR" value={eur ? money(eur.total) : "—"}
          icon={<BarChart3 size={20}/>} detail="EUR uniquement · hors documents rejetés"/>
        <StatCard label="Fournisseurs · EUR" value={eur?.supplier_count ?? "—"}
          icon={<BadgeCheck size={20}/>} detail="Fournisseurs de factures EUR validées"/>
        <StatCard label="Taux de rejet" value={percent(rejected, total)}
          icon={<FileX2 size={20}/>} detail="Documents rejetés / tous les documents"/>
      </div>}
    </section>
    {!ready ? <Pane className="analytics-unavailable"><EmptyState icon="chart" title="Analyse indisponible dans cette instance"
      description={demo
        ? "La démonstration publique ne contient que trois métadonnées fictives. Aucune facture, dépense ni KPI D3 n'y est calculé."
        : data?.reason ?? "Les indicateurs PostgreSQL ne sont pas disponibles pour le moment."}/></Pane> :
    <>
      <div className="analytics-grid">
        <Pane title="Dépenses dans le temps" subtitle="Date de facture · montant TTC · EUR">
          <MonthlyChart rows={monthly}/>
        </Pane>
        <Pane title="Dépenses par fournisseur" subtitle="Factures acceptées · EUR">
          <SupplierBars rows={suppliers}/>
        </Pane>
        <Pane title="Qualité documentaire" subtitle="Comptes calculés sur les documents importés">
          <StatusDonut accepted={overview?.processed ?? 0} rejected={rejected}
            received={Math.max(0, total - (overview?.processed ?? 0) - rejected)}/>
          <div className="subtle-divider"/>
          <Hint>Le taux porte sur les documents, pas sur les lignes de factures.</Hint>
        </Pane>
      </div>
      <div className="analytics-bottom-grid">
        <Pane title="Réconciliation par devise" subtitle="Chaque devise conserve son unité — aucune conversion implicite">
          <div className="table-overflow">
            <table className="data-table compact-table">
              <thead><tr><th>Devise</th><th>Factures</th><th>HT</th><th>TVA</th><th>TTC</th></tr></thead>
              <tbody>{data!.currencies.map(item => <tr key={item.currency}>
                <td><strong>{item.currency}</strong></td><td>{item.invoice_count}</td>
                <td>{money(item.subtotal, item.currency)}</td>
                <td>{money(item.tax, item.currency)}</td>
                <td><strong>{money(item.total, item.currency)}</strong></td>
              </tr>)}</tbody>
            </table>
          </div>
          {!data!.currencies.length && <EmptyState icon="chart" title="Aucune facture validée" description="Importe et traite un document pour alimenter les vues SQL."/>}
        </Pane>
        <Pane title="Anomalies détectées" subtitle="Contrôles sur les sources documentaires">
          {data!.issues.length ? <div className="issue-bars">{data!.issues.slice(0, 7).map(row =>
            <div className="issue-bar-item" key={`${row.code}-${row.severity}`}>
              <div><CircleHelp size={15}/><span title={row.code}>{issueLabel(row.code)}<small>{row.code}</small></span></div>
              <strong>{row.count}</strong>
            </div>)}</div> :
          <EmptyState icon="alert" title="Aucune anomalie signalée" description="Les diagnostics de D2 apparaîtront ici."/>}
        </Pane>
      </div>
    </>}
  </div>;
}
