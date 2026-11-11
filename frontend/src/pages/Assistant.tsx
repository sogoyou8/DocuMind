import { useEffect, useRef, useState } from "react";
import {
  ArrowUp, BookOpenCheck, BrainCircuit, CheckCheck, ChevronRight,
  Cpu, FileSearch, FileText, Fingerprint, LockKeyhole, MessageCircle,
  SearchCheck, ShieldCheck, Sparkles,
} from "lucide-react";
import type { AssistantAnswer, AssistantStatus } from "../types";
import { Hint, LabelPill, Pane } from "../components/Visuals";
import { applicationHelp, displayedAnswer, sourceLabel } from "../ux";

type Message = {
  id: number;
  question: string;
  response?: AssistantAnswer;
  guide?: string;
  error?: string;
};

const suggestions = [
  "Quel est le montant TTC de la facture DM-2026-001 ?",
  "Quel fournisseur apparaît sur la facture DM-2026-001 ?",
  "Quel est le numéro de la facture présente dans le document ?",
];

// Every example pre-fills the composer. It never generates a sample answer or
// assumes that a requested document exists in the local, indexed corpus.
const requestExamples = [
  { title: "Résumer une facture",
    question: "Résume la facture DM-2026-001 à partir de ses passages indexés et cite les sources." },
  { title: "Retrouver une TVA",
    question: "Quel est le montant de TVA indiqué dans la facture DM-2026-001 ? Cite la source." },
  { title: "Identifier un fournisseur",
    question: "Quel fournisseur est mentionné dans la facture DM-2026-001 ? Cite la source." },
  { title: "Vérifier une source",
    question: "Dans quel document et à quelle ligne ou page se trouve le montant TTC de la facture DM-2026-001 ?" },
] as const;

export default function AssistantView({
  enabled, demo, status, onAsk, onCitation,
}: {
  enabled: boolean;
  demo: boolean;
  status: AssistantStatus | null;
  onAsk: (question: string) => Promise<AssistantAnswer>;
  onCitation: (documentId: string) => void;
}) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const messageSequence = useRef(0);
  const canAsk = enabled && !demo;
  const prepareQuestion = (value: string) => {
    setQuestion(value);
    composer.current?.focus();
  };
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, busy]);

  const ask = async (value?: string) => {
    const text = (value ?? question).trim();
    if (!canAsk || busy || text.length < 4 || text.length > 500) return;
    const id = ++messageSequence.current;
    setQuestion("");
    const guide = applicationHelp(text);
    if (guide) {
      setMessages(old => [...old, { id, question: text, guide }]);
      return;
    }
    setMessages(old => [...old, { id, question: text }]);
    setBusy(true);
    try {
      const response = await onAsk(text);
      setMessages(old => old.map(item => item.id === id ? { ...item, response } : item));
    } catch (error) {
      setMessages(old => old.map(item => item.id === id
        ? { ...item, error: error instanceof Error ? error.message : "Une erreur est survenue." }
        : item));
    } finally {
      setBusy(false);
    }
  };

  return <div className="page-stack assistant-page assistant-premium-page">
    <header className="assistant-premium-hero glass">
      <div className="assistant-hero-content">
        <div className="eyebrow"><span className="signal-pulse"/> ASSISTANT / RAG LOCAL D4</div>
        <h1>Parlez à vos <span>documents</span></h1>
        <p>Des réponses liées à leurs sources — jamais un texte généré sans contrôle.</p>
      </div>
      <div className="assistant-hero-art" aria-hidden="true">
        <div className="assistant-hero-orbit"/>
        <div className="assistant-hero-doc assistant-hero-doc-back"/>
        <div className="assistant-hero-doc assistant-hero-doc-middle"/>
        <div className="assistant-hero-doc assistant-hero-doc-front">
          <BrainCircuit size={26}/><i/><i/><i/>
        </div>
      </div>
      <LabelPill kind={canAsk && status?.enabled ? "good" : "neutral"}>
        <span className="inline-icon">{canAsk && status?.enabled ? <CheckCheck size={14}/> : <LockKeyhole size={14}/>}
          {canAsk && status?.enabled ? "Ollama local prêt" : demo ? "Désactivé en démo" : "IA locale indisponible"}</span>
      </LabelPill>
    </header>
    <div className="assistant-grid assistant-premium-grid">
      <Pane className="assistant-main assistant-premium-main">
        <div className="assistant-conversation" aria-live="polite">
          {!messages.length ? <div className="assistant-empty assistant-premium-empty">
            <div className="assistant-symbol-stage" aria-hidden="true">
              <span className="assistant-symbol"><BrainCircuit size={35}/></span>
            </div>
            <div className="eyebrow">UN ASSISTANT, DES PREUVES</div>
            <h2>Que souhaitez-vous comprendre ?</h2>
            <p>Interrogez les documents validés. Chaque citation indique précisément le fichier et la ligne ou page d'origine.</p>
            <div className="assistant-prompts">
              {suggestions.map(s => <button key={s} type="button" disabled={!canAsk}
                onClick={() => prepareQuestion(s)} title="Placer la question dans le champ de saisie"><Sparkles size={14}/><span>{s}</span><ChevronRight size={15}/></button>)}
            </div>
            <div className="assistant-guidance">
              <span>Les suggestions remplissent le champ sans envoyer de demande.</span>
              <button type="button" disabled={!canAsk} onClick={() => prepareQuestion("Que peux-tu faire ?")}>Découvrir DocuMind</button>
            </div>
          </div> :
            <div className="messages">
              {messages.map(msg => <div key={msg.id} className="message-group">
                <div className="message user-message"><span className="message-avatar user-avatar">VO</span>
                  <p>{msg.question}</p></div>
                {msg.response || msg.guide ? <div className="assistant-reply">
                  <span className="message-avatar ai-avatar"><BrainCircuit size={17}/></span>
                  <div className="reply-body">
                    <div className="reply-top"><strong>DocuMind</strong>
                      <LabelPill kind={msg.guide ? "info" : msg.response?.status === "answered" ? "good" : "neutral"}>
                        {msg.guide ? "Guide de l'application" : msg.response?.status === "answered" ? "Réponse sourcée" : "Abstention"}
                      </LabelPill></div>
                    <p>{msg.guide ?? displayedAnswer(msg.question, msg.response?.answer ?? "", msg.response?.citations ?? [])}</p>
                    {msg.response && msg.response.citations.length > 0 && <div className="citation-list">
                      <span className="citation-heading"><BookOpenCheck size={14}/> Sources vérifiées</span>
                      {msg.response.citations.map(citation => <div className="citation-card" key={citation.id}>
                        <button type="button" className="citation-open"
                          aria-label={`Ouvrir la fiche source ${citation.document}`}
                          onClick={() => onCitation(citation.document_id)}>
                          <FileSearch size={17}/><strong>{citation.document}</strong><ChevronRight size={15}/>
                        </button>
                        <div className="citation-meta">
                          <span title={citation.source_locator}>{sourceLabel(citation.source_locator)}</span>
                          <code>{citation.id}</code>
                        </div>
                        <p className="citation-preview">{citation.excerpt}</p>
                        <details className="citation-details">
                          <summary>Consulter l'extrait complet</summary>
                          <p>{citation.excerpt}</p>
                          <small>Identifiant technique : {citation.source_locator}</small>
                        </details>
                      </div>)}
                    </div>}
                    {msg.response?.status === "abstained" && <Hint>
                      Aucun passage vérifié ne permet d'étayer cette demande. Reformule la question ou importe un document pertinent.
                    </Hint>}
                  </div>
                </div> : msg.error ? <div className="message-error" role="alert">{msg.error}</div>
                  : <div className="thinking"><span/><span/><span/> Analyse des sources…</div>}
              </div>)}
              <div ref={bottom}/>
            </div>}
        </div>
        <div className="assistant-compose">
          {!canAsk && <div className="assistant-disabled"><LockKeyhole size={15}/>
            {demo ? "L'assistant n'est pas exécuté sur Render. Ouvre la V1 locale pour l'utiliser." :
              "Démarre le profil Docker IA et connecte-toi à l'instance RAG."}</div>}
          <form onSubmit={event => { event.preventDefault(); void ask(); }} className="assistant-form">
            <label htmlFor="assistant-question" className="sr-only">Poser une question documentaire</label>
            <textarea ref={composer} id="assistant-question" value={question} rows={2} maxLength={500}
              disabled={!canAsk || busy}
              placeholder={canAsk ? "Posez une question sur les documents acceptés…" : "Assistant disponible uniquement en local"}
              onChange={event => setQuestion(event.target.value)}
              onKeyDown={event => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void ask();
                }
              }}/>
            <button className="send-button" type="submit" disabled={!canAsk || busy || question.trim().length < 4}
              aria-label="Envoyer la question"><ArrowUp size={20}/></button>
          </form>
          <div className="compose-footer"><span>Entrée pour envoyer · Maj + Entrée pour une nouvelle ligne</span>
            <span>{question.length}/500</span></div>
        </div>
      </Pane>
      <div className="assistant-side assistant-premium-side">
        <Pane className="assistant-engine-pane" title="Moteur documentaire" subtitle="Exécution privée et vérifiable">
          <div className="assistant-engine-stats">
            <div className="model-block"><div className="model-icon"><Cpu size={20}/></div>
              <div><small>Modèle de génération</small><strong>{status?.generation_model ?? "—"}</strong></div></div>
            <div className="model-block"><div className="model-icon"><Fingerprint size={20}/></div>
              <div><small>Modèle d'embedding</small><strong>{status?.embedding_model ?? "—"}</strong></div></div>
            <div className="model-block"><div className="model-icon"><BookOpenCheck size={20}/></div>
              <div><small>Passages indexés</small><strong>{status?.indexed_chunks ?? "—"}</strong></div></div>
          </div>
          <div className="subtle-divider"/>
          <div className="model-note"><ShieldCheck size={17}/> Aucune API IA externe nécessaire.</div>
        </Pane>
        <Pane className="assistant-workflow-pane" title="Ce que l'assistant fait" subtitle="Un circuit fermé, sans outil arbitraire">
          <div className="trust-steps assistant-steps">
            <div><span><FileSearch size={17}/></span><p><strong>Recherche</strong><small>Chroma + documents acceptés</small></p></div>
            <div><span><MessageCircle size={17}/></span><p><strong>Réponse</strong><small>Ollama et LangGraph locaux</small></p></div>
            <div><span><ShieldCheck size={17}/></span><p><strong>Vérification</strong><small>Empreinte et citations SQL</small></p></div>
          </div>
          <div className="assistant-safety-note" role="note">
            <ShieldCheck size={15}/>
            <span>Une réponse IA peut être incorrecte malgré ses citations. Vérifiez les extraits avant toute décision importante.</span>
          </div>
        </Pane>
        <Pane className="assistant-examples-pane" title="Exemples de demandes"
          subtitle="Des questions pour commencer, sans envoi automatique">
          <div className="assistant-request-grid">
            {requestExamples.map((item, index) => <button key={item.title} type="button"
              disabled={!canAsk || busy}
              title="Préparer cette question sans l'envoyer"
              onClick={() => prepareQuestion(item.question)}>
              {index === 0 ? <FileText size={18}/> :
                index === 1 ? <SearchCheck size={18}/> :
                  index === 2 ? <Fingerprint size={18}/> : <BookOpenCheck size={18}/>}
              <span>{item.title}</span>
              <ChevronRight size={15}/>
            </button>)}
          </div>
        </Pane>
      </div>
    </div>
  </div>;
}
