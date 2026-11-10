import { AlertTriangle, CheckCircle2, Clock3, FilePlus2, Fingerprint, ListChecks, ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { Audit } from "../types";
import { eventDate, eventLabel, eventTone } from "../ux";
import { EmptyState, Hint, Pane } from "../components/Visuals";

export default function ActivityView({
  events, count, demo, onDocument,
}: { events: Audit[]; count: number; demo: boolean; onDocument: (id: string) => void }) {
  const [search, setSearch] = useState("");
  const filtered = events.filter(item =>
    `${eventLabel(item.action)} ${item.action} ${item.document_name} ${item.actor ?? "Système"}`
      .toLocaleLowerCase("fr").includes(search.trim().toLocaleLowerCase("fr")),
  );
  return <div className="page-stack activity-page">
    <div className="page-intro">
      <div><div className="eyebrow">PREUVES / JOURNAL D'AUDIT</div>
        <h1>Historique des opérations</h1>
        <p>Un suivi horodaté des imports, validations et indexations documentaires.</p>
      </div>
      <span className="muted-pill"><Clock3 size={15}/>{demo ? "Démo sans événements" : `${count} événement(s)`}</span>
    </div>
    <Pane className="activity-pane" title="Journal documentaire"
      subtitle={demo ? "Aucun traitement exécuté sur Render" : `${events.length} dernier(s) événement(s) disponibles sur ${count}`}
      aside={<ListChecks className="muted-icon" size={18}/>}>
      {!demo && <div className="table-toolbar activity-toolbar">
        <label className="search-field"><Fingerprint size={16}/>
          <input type="search" aria-label="Filtrer l'historique"
            placeholder="Action, document, acteur…" value={search} onChange={e => setSearch(e.target.value)}/>
        </label>
        <span className="activity-filter-counter">{filtered.length} événement(s) affiché(s)</span>
      </div>}
      <div className="activity-timeline-scroll">
        {filtered.length ? <div className="timeline">
          {filtered.map(entry => {
            const tone = eventTone(entry.action);
            const Icon = tone === "danger" ? AlertTriangle
              : tone === "good" ? CheckCircle2 : FilePlus2;
            return <button key={entry.id} className={`timeline-entry timeline-${tone}`} type="button"
              onClick={() => onDocument(entry.document_id)}
              aria-label={`Ouvrir ${entry.document_name} : ${eventLabel(entry.action)}`}>
              <span className="timeline-mark"><Icon size={17}/></span>
              <div className="timeline-body">
                <div className="timeline-heading">
                  <strong title={entry.action}>{eventLabel(entry.action)}</strong>
                  <time dateTime={entry.created_at}>{eventDate(entry.created_at)}</time>
                </div>
                <p>{entry.document_name}</p>
                <span>Acteur : {entry.actor ?? "Système"}</span>
              </div>
            </button>;
          })}
        </div> : <EmptyState title={demo ? "Aucun événement dans la démo" : "Aucun événement correspondant"}
          icon="document" description={demo
            ? "Le service Render n'exécute aucun import, pipeline ou indexation."
            : "Aucun des événements chargés ne correspond au filtre."}/>}
      </div>
      {!demo && count > events.length && <Hint>La recherche porte sur les {events.length} dernières entrées chargées (maximum 40), pas sur tout l'historique PostgreSQL.</Hint>}
    </Pane>
    <div className="metric-contract glass activity-contract"><ShieldCheck size={18}/>
      <p>Journal issu du backend Django : aucun événement, acteur ou statut d'exécution inventé.</p>
    </div>
  </div>;
}
