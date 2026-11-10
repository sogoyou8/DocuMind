import type { ReactNode } from "react";
import {
  AlertTriangle, ArrowUpRight, CircleCheck, CircleHelp,
  DatabaseZap, FileText, FolderOpen, ShieldCheck,
} from "lucide-react";
import type { DocState, Monthly, Supplier } from "../types";
import { money, monthName, stateLabels } from "../format";

export function StatusChip({ state }: { state: DocState }) {
  const kind = state === "INDEXED" || state === "ACCEPTED" ? "good"
    : state === "REJECTED" ? "danger"
      : state === "VALIDATING" ? "info" : "neutral";
  return <span className={`status-chip ${kind}`}><i aria-hidden="true"/>{stateLabels[state]}</span>;
}

export function LabelPill({
  children, kind = "neutral",
}: { children: ReactNode; kind?: "neutral" | "good" | "info" | "danger" }) {
  return <span className={`label-pill ${kind}`}>{children}</span>;
}

export function StatCard({
  label, value, icon, detail, accent = false,
}: {
  label: string;
  value: string | number;
  icon: ReactNode;
  detail: string;
  accent?: boolean;
}) {
  return <article className={`stat-card glass ${accent ? "stat-accent" : ""}`}>
    <div className="stat-heading"><span>{label}</span><span className="stat-icon">{icon}</span></div>
    <div className="stat-value" title={String(value)}>{value}</div>
    <div className="stat-caption">{detail}</div>
  </article>;
}

export function Pane({
  children, className = "", title, subtitle, aside,
}: {
  children: ReactNode; className?: string;
  title?: string; subtitle?: string; aside?: ReactNode;
}) {
  return <section className={`glass pane ${className}`}>
    {title && <div className="pane-top">
      <div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>
      {aside && <div className="pane-aside">{aside}</div>}
    </div>}
    {children}
  </section>;
}

export function EmptyState({
  title, description, icon = "document",
}: { title: string; description: string; icon?: "document" | "chart" | "alert" | "shield" }) {
  const Icon = icon === "chart" ? DatabaseZap : icon === "alert" ? AlertTriangle
    : icon === "shield" ? ShieldCheck : FolderOpen;
  return <div className="empty-state" role="status">
    <span className="empty-icon"><Icon size={23}/></span>
    <strong>{title}</strong><p>{description}</p>
  </div>;
}

export function MonthlyChart({ rows }: { rows: Monthly[] }) {
  if (!rows.length) return <EmptyState icon="chart" title="Pas de dépenses disponibles" description="Les montants apparaîtront après validation de factures dans PostgreSQL."/>;
  const numbers = rows.map(r => Math.max(0, Number(r.total) || 0));
  const rawMax = Math.max(1, ...numbers);
  const step = Math.max(1, Math.ceil(rawMax / 40) * 10);
  const top = step * 4;
  const left = 71, right = 621, topMargin = 19, bottom = 160;
  const points = numbers.map((v, i) => ({
    x: rows.length === 1 ? (left + right) / 2
      : left + (right - left) * i / (rows.length - 1),
    y: bottom - (v / top) * (bottom - topMargin),
    amount: rows[i].total,
    period: rows[i].month,
  }));
  const poly = points.map(p => `${p.x},${p.y}`).join(" ");
  const area = `M ${points[0].x} ${bottom} L ${points.map(p => `${p.x} ${p.y}`).join(" L ")} L ${points[points.length - 1].x} ${bottom} Z`;
  return <div className="chart-wrap">
    <svg viewBox="0 0 656 210" className="line-chart" role="img" aria-label={`Dépenses mensuelles en euros. ${rows.map(r => `${monthName(r.month)} : ${money(r.total)}`).join(", ")}`}>
      <defs>
        <linearGradient id="monthly-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#60f5d0" stopOpacity=".25"/>
          <stop offset="100%" stopColor="#60f5d0" stopOpacity="0"/>
        </linearGradient>
      </defs>
      {[0, .25, .5, .75, 1].map(t => <g key={t}>
        <line x1={left} x2={right} y1={bottom - t * (bottom - topMargin)}
          y2={bottom - t * (bottom - topMargin)} stroke="#768c9f" strokeOpacity=".23" strokeDasharray="5 7"/>
        <text x={left - 9} y={bottom - t * (bottom - topMargin) + 4}
          fontSize="11" textAnchor="end" fill="#adbfca">
          {new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 }).format(top * t)} €
        </text>
      </g>)}
      <path d={area} fill="url(#monthly-fill)"/>
      {points.length > 1 && <polyline fill="none" stroke="#78f3d1" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" points={poly}/>}
      {points.map(p => <g key={p.period}>
        <circle cx={p.x} cy={p.y} r="5" fill="#101c25" stroke="#83f8d7" strokeWidth="2.5"/>
        <title>{`${monthName(p.period)} — ${money(p.amount)}`}</title>
        <text x={p.x} y="193" textAnchor="middle" fontSize="12" fill="#91a6b5">{monthName(p.period)}</text>
        {points.length === 1 && <text x={p.x} y={p.y - 14} textAnchor="middle" fontSize="12" fill="#a7ffe6">{money(p.amount)}</text>}

      </g>)}
    </svg>
    <div className="chart-foot">
      <span><i className="dot-mint" aria-hidden="true"/> Montants TTC validés</span>
      <span>Devise : EUR</span>
    </div>
  </div>;
}

export function SupplierBars({ rows }: { rows: Supplier[] }) {
  if (!rows.length) return <EmptyState icon="chart" title="Aucun fournisseur" description="Aucune facture validée en euros pour cette sélection."/>;
  const max = Math.max(1, ...rows.map(r => Number(r.total)));
  return <div className="supplier-bars">
    {rows.slice(0, 5).map((row, index) => <div className="supplier-row" key={`${row.supplier_name}-${row.currency}`}>
      <div className="supplier-label"><span className="supplier-index">{String(index + 1).padStart(2, "0")}</span>
        <span title={row.supplier_name}>{row.supplier_name}</span><strong>{money(row.total, row.currency)}</strong></div>
      <div className="bar-track" role="img" aria-label={`${row.supplier_name}: ${money(row.total, row.currency)}`}>
        <span className="bar-fill" style={{ width: `${Math.max(0, 100 * Number(row.total) / max)}%` }}/>
      </div>
    </div>)}
  </div>;
}

export function StatusDonut({
  accepted, received, rejected,
}: { accepted: number; received: number; rejected: number }) {
  const total = Math.max(0, accepted + received + rejected);
  const a = total ? accepted / total * 100 : 0;
  const b = total ? (accepted + rejected) / total * 100 : 0;
  return <div className="donut-layout">
    <div className="donut" role="img" aria-label={`${accepted} acceptés, ${rejected} rejetés, ${received} en attente`}
      style={{ background: total
        ? `conic-gradient(#68eac6 0% ${a}%, #fa987e ${a}% ${b}%, #49718d ${b}% 100%)`
        : "conic-gradient(#273744 0% 100%)" }}>
      <div className="donut-core"><strong>{total}</strong><span>documents</span></div>
    </div>
    <div className="donut-legend">
      <span><i className="legend-dot accepted"/> Acceptés / indexés <strong>{accepted}</strong></span>
      <span><i className="legend-dot rejected"/> Rejetés <strong>{rejected}</strong></span>
      <span><i className="legend-dot pending"/> En attente <strong>{received}</strong></span>
    </div>
  </div>;
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return <div className="detail-field"><span>{label}</span><strong>{children}</strong></div>;
}

export function Hint({ children, warning = false }: { children: ReactNode; warning?: boolean }) {
  return <div className={`hint ${warning ? "warning" : ""}`}><CircleHelp size={15}/><p>{children}</p></div>;
}

export const icons = { FileText, CircleCheck, ArrowUpRight };
