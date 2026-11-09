import { useEffect, useRef, useState } from "react";
import {
  ArrowUp, BookOpenCheck, BrainCircuit, CheckCheck, ChevronRight,
  Cpu, FileSearch, Fingerprint, LockKeyhole, MessageCircle,
  ShieldCheck, Sparkles,
} from "lucide-react";
import type { AssistantAnswer, AssistantStatus } from "../types";
import { Hint, LabelPill, Pane } from "../components/Visuals";

type Message = {
  id: number;
  question: string;
  response?: AssistantAnswer;
  error?: string;
};

const suggestions = [
  "Quel est le montant TTC de la facture DM-2026-001 ?",
  "Quel fournisseur apparaît sur la facture DM-2026-001 ?",
  "Quel est le numéro de la facture présente dans le document ?",
];

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
  const canAsk = enabled && !demo;
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, busy]);

  const ask = async (value?: string) => {
    const text = (value ?? question).trim();
    if (!canAsk || busy || text.length < 4 || text.length > 500) return;
    const id = Date.now();
    setQuestion("");
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

  return <div className="page-stack assistant-page">
    <div className="page-intro">
      <div><div className="eyebrow">ASSISTANT / RAG LOCAL D4</div><h1>Parlez à vos documents</h1>
        <p>Des réponses liées à leurs sources — jamais un texte généré sans contrôle.</p></div>
      <LabelPill kind={canAsk && status ? "good" : "neutral"}>
        <span className="inline-icon">{canAsk && status ? <CheckCheck size={14}/> : <LockKeyhole size={14}/>}
          {canAsk && status ? "Ollama local prêt" : demo ? "Désactivé en démo" : "IA locale indisponible"}</span>
      </LabelPill>
    </div>
    <div className="assistant-grid">
      <Pane className="assistant-main">
        <div className="assistant-conversation" aria-live="polite">
          {!messages.length ? <div className="assistant-empty">
            <span className="assistant-symbol"><BrainCircuit size={35}/></span>
            <div className="eyebrow">UN ASSISTANT, DES PREUVES</div>
            <h2>Que souhaitez-vous comprendre ?</h2>
            <p>Interrogez les documents validés. Chaque citation indique précisément le fichier et la ligne ou page d'origine.</p>
            <div className="assistant-prompts">
              {suggestions.map(s => <button key={s} type="button" disabled={!canAsk}
                onClick={() => setQuestion(s)}><Sparkles size={14}/><span>{s}</span><ChevronRight size={15}/></button>)}
            </div>
          </div> :
            <div className="messages">
              {messages.map(msg => <div key={msg.id} className="message-group">
                <div className="message user-message"><span className="message-avatar user-avatar">VO</span>
                  <p>{msg.question}</p></div>
                {msg.response ? <div className="assistant-reply">
                  <span className="message-avatar ai-avatar"><BrainCircuit size={17}/></span>
                  <div className="reply-body">
                    <div className="reply-top"><strong>DocuMind</strong>
                      <LabelPill kind={msg.response.status === "answered" ? "good" : "neutral"}>
                        {msg.response.status === "answered" ? "Réponse sourcée" : "Abstention"}
                      </LabelPill></div>
                    <p>{msg.response.answer}</p>
                    {msg.response.citations.length > 0 && <div className="citation-list">
                      <span className="citation-heading"><BookOpenCheck size={14}/> Sources vérifiées</span>
                      {msg.response.citations.map(citation => <button key={citation.id} type="button"
                        className="citation-card" onClick={() => onCitation(citation.document_id)}>
                        <div><FileSearch size={17}/><strong>{citation.document}</strong><span>{citation.id}</span></div>
                        <small>{citation.source_locator}</small>
                        <p>{citation.excerpt}</p>
                      </button>)}
                    </div>}
                    {msg.response.status === "abstained" && <Hint>
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
            <textarea id="assistant-question" value={question} rows={2} maxLength={500}
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
      <div className="assistant-side">
        <Pane title="Moteur documentaire" subtitle="Exécution privée et vérifiable">
          <div className="model-block"><div className="model-icon"><Cpu size={20}/></div>
            <div><small>Modèle de génération</small><strong>{status?.generation_model ?? "—"}</strong></div></div>
          <div className="model-block"><div className="model-icon"><Fingerprint size={20}/></div>
            <div><small>Modèle d'embedding</small><strong>{status?.embedding_model ?? "—"}</strong></div></div>
          <div className="model-block"><div className="model-icon"><BookOpenCheck size={20}/></div>
            <div><small>Passages indexés</small><strong>{status?.indexed_chunks ?? "—"}</strong></div></div>
          <div className="subtle-divider"/>
          <div className="model-note"><ShieldCheck size={17}/> Aucune API IA externe nécessaire.</div>
        </Pane>
        <Pane title="Ce que l'assistant fait" subtitle="Un circuit fermé, sans outil arbitraire">
          <div className="trust-steps assistant-steps">
            <div><span><FileSearch size={17}/></span><p><strong>Recherche</strong><small>Chroma + documents acceptés</small></p></div>
            <div><span><MessageCircle size={17}/></span><p><strong>Réponse</strong><small>Ollama et LangGraph locaux</small></p></div>
            <div><span><ShieldCheck size={17}/></span><p><strong>Vérification</strong><small>Empreinte et citations SQL</small></p></div>
          </div>
        </Pane>
        <Hint warning>Une réponse IA peut être incorrecte malgré ses citations. Vérifiez les extraits sources pour les décisions importantes.</Hint>
      </div>
    </div>
  </div>;
}
