import { Activity, Clock3, Fingerprint, ListChecks, ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { Audit } from "../types";
import { shortDate } from "../format";
import { EmptyState, Hint, Pane } from "../components/Visuals";

export default function ActivityView({
  events, count, demo, onDocument,
}: { events: Audit[]; count: number; demo: boolean; onDocument: (id: string) => void }) {
  const [search, setSearch] = useState("");
  const filtered = events.filter(item =>
    `${item.action} ${item.document_name} ${item.actor ?? ""}`
      .toLocaleLowerCase("fr").includes(search.trim().toLocaleLowerCase("fr")),
  );
  return <div className="page-stack">
    <div className="page-intro">
      <div><div className="eyebrow">PREUVES / JOURNAL D'AUDIT</div>
        <h1>Historique des opérations</h1>
        <p>Un suivi horodaté des imports, validations et indexations documentaires.</p>
      </div><span className="muted-pill"><Clock3 size={15}/> {demo ? "Démo sans événements" : `${count} événement(s)`}</span>
    </div>
    <Pane title="Journal documentaire" subtitle={demo ? "Aucun traitement exécuté sur Render" : `Les ${events.length} dernières entrées disponibles`}
      aside={<ListChecks className="muted-icon" size={18}/>}>
      {!demo && <div className="table-toolbar"><label className="search-field">
        <Fingerprint size={16}/><input type="search" aria-label="Filtrer l'historique"
          placeholder="Action, document, acteur…" value={search} onChange={e => setSearch(e.target.value)}/>
      </label></div>}
      {filtered.length ? <div className="timeline">
        {filtered.map(entry => <button key={entry.id} className="timeline-entry" type="button"
          onClick={() => onDocument(entry.document_id)}>
          <span className="timeline-mark"><Activity size={17}/></span>
          <div><div className="timeline-heading"><strong>{entry.action}</strong><small>{shortDate(entry.created_at)}</small></div>
            <p>{entry.document_name}</p><span>Acteur : {entry.actor ?? "Système"}</span>
          </div></button>)}
      </div> : <EmptyState title={demo ? "Aucun événement dans la démo" : "Aucun événement correspondant"}
        icon="document" description={demo
          ? "Le service Render n'exécute aucun import, pipeline ou indexation."
          : "Les opérations réelles sont enregistrées dans PostgreSQL et apparaîtront ici."}/>}
      {!demo && count > events.length && <Hint>Seules les {events.length} dernières entrées sont affichées pour préserver une interface lisible.</Hint>}
    </Pane>
    <div className="metric-contract glass"><ShieldCheck size={18}/>
      <p>Le journal reflète les événements stockés par le backend. Il n'invente aucun statut d'exécution ni aucune action utilisateur.</p></div>
  </div>;
}
