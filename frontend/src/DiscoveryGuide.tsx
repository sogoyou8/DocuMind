import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, ArrowLeft, ArrowRight, BookOpenCheck, BrainCircuit, CheckCheck,
  ChevronRight, CircleHelp, FileCheck2, Files, Fingerprint, LayoutDashboard,
  MousePointerClick, ShieldCheck, Sparkles, Upload, X, BarChart3,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { Tab } from "./types";
import { beginnerRoute, discoveryPage, discoveryPages, discoveryRoute } from "./discovery-data";

type Mode = "home" | "lesson" | "spotlight";
type Rectangle = { top: number; left: number; width: number; height: number };
type Props = {
  currentPage: Tab;
  onNavigate: (page: Tab) => void;
  onClose: () => void;
  demo: boolean;
  operator: boolean;
  aiEnabled: boolean;
};

const icons = {
  overview: LayoutDashboard,
  documents: Files,
  analytics: BarChart3,
  assistant: BrainCircuit,
  activity: Activity,
} satisfies Record<Tab, LucideIcon>;

const topics = [
  { label: "Importer", icon: Upload },
  { label: "Contrôler D2", icon: ShieldCheck },
  { label: "Analyser", icon: BarChart3 },
  { label: "Indexer", icon: FileCheck2 },
  { label: "Interroger", icon: Sparkles },
] as const;

function GuidanceRestriction({ page, demo, operator, aiEnabled }: {
  page: Tab; demo: boolean; operator: boolean; aiEnabled: boolean;
}) {
  const message = demo
    ? "La démonstration publique est en lecture seule : le guide montre le parcours local, sans lancer de traitement."
    : page === "documents" && !operator
      ? "Votre session est en consultation. L'import et le traitement nécessitent le rôle opérateur."
      : page === "assistant" && !aiEnabled
        ? "L'Assistant IA nécessite le profil local Ollama/Chroma et des documents indexés."
        : null;
  return message ? <div className="discovery-limitation" role="note">
    <CircleHelp size={15}/>{message}
  </div> : null;
}

function PageGlyph({ page }: { page: Tab }) {
  const Icon = icons[page];
  return <span className="discovery-glyph"><Icon size={21}/></span>;
}

/** The overlay never sends requests, invokes D2 or submits a question. */
export default function DiscoveryGuide({ currentPage, onNavigate, onClose, demo, operator, aiEnabled }: Props) {
  const [mode, setMode] = useState<Mode>("home");
  const [pageId, setPageId] = useState<Tab>("overview");
  const [stepIndex, setStepIndex] = useState(0);
  const [beginner, setBeginner] = useState(false);
  const [frame, setFrame] = useState<Rectangle | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const dialogRef = useRef<HTMLElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const initialFocus = useRef<HTMLElement | null>(null);
  const page = useMemo(() => discoveryPage(pageId), [pageId]);
  const step = page.steps[stepIndex];
  const order = beginner ? beginnerRoute : discoveryRoute;
  const currentPageIndex = order.indexOf(pageId);
  const last = currentPageIndex === order.length - 1 &&
    stepIndex === page.steps.length - 1;

  useEffect(() => {
    initialFocus.current = document.activeElement as HTMLElement | null;
    return () => initialFocus.current?.focus();
  }, []);

  useEffect(() => {
    if (mode === "spotlight") tooltipRef.current?.focus();
    else dialogRef.current?.focus();
  }, [mode, pageId, stepIndex]);

  useEffect(() => {
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopImmediatePropagation();
        onClose();
        return;
      }
      if (event.key !== "Tab" || mode === "spotlight") return;
      const dialog = dialogRef.current;
      if (!dialog) return;
      const focusable = Array.from(dialog.querySelectorAll<HTMLElement>(
        'button:not(:disabled), a[href], [tabindex]:not([tabindex="-1"])',
      )).filter(el => el.getClientRects().length && !el.hasAttribute("hidden"));
      if (!focusable.length) { event.preventDefault(); dialog.focus(); return; }
      const first = focusable[0], lastButton = focusable[focusable.length - 1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog)) {
        event.preventDefault();
        lastButton.focus();
      } else if (!event.shiftKey && document.activeElement === lastButton) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", keydown, true);
    return () => window.removeEventListener("keydown", keydown, true);
  }, [mode, onClose]);

  const choosePage = useCallback((id: Tab) => {
    setBeginner(false);
    setPageId(id);
    setStepIndex(0);
    setFrame(null);
    setMode("lesson");
  }, []);
  const startBeginner = () => {
    setBeginner(true);
    setPageId("documents");
    setStepIndex(0);
    setFrame(null);
    setMode("lesson");
  };

  const next = useCallback(() => {
    if (stepIndex < page.steps.length - 1) {
      setStepIndex(old => old + 1);
    } else if (currentPageIndex < order.length - 1) {
      setPageId(order[currentPageIndex + 1]);
      setStepIndex(0);
      if (mode === "spotlight") onNavigate(order[currentPageIndex + 1]);
    } else {
      onClose();
    }
  }, [stepIndex, page.steps.length, currentPageIndex, mode, order, onNavigate, onClose]);

  const previous = useCallback(() => {
    if (stepIndex > 0) setStepIndex(old => old - 1);
    else if (currentPageIndex > 0) {
      const previousPage = order[currentPageIndex - 1];
      setPageId(previousPage);
      setStepIndex(discoveryPage(previousPage).steps.length - 1);
      if (mode === "spotlight") onNavigate(previousPage);
    } else setMode("home");
  }, [stepIndex, currentPageIndex, mode, order, onNavigate]);

  const showInApp = () => {
    onNavigate(pageId);
    setFrame(null);
    setMode("spotlight");
  };

  // If the user follows a real in-app link and changes page, show the guide
  // again instead of leaving a spotlight over an unrelated screen.
  useEffect(() => {
    if (mode === "spotlight" && currentPage !== pageId) {
      setFrame(null);
      setMode("lesson");
    }
  }, [mode, currentPage, pageId]);

  useEffect(() => {
    if (mode !== "spotlight") return;
    let raf = 0;
    let timeout = 0;
    let active = true;
    const select = () => {
      const matching = document.querySelector<HTMLElement>(step.target);
      const fallback = step.fallback ? document.querySelector<HTMLElement>(step.fallback) : null;
      const candidate = matching && matching.getClientRects().length ? matching : fallback;
      return candidate && candidate.getClientRects().length ? candidate : null;
    };
    const measure = () => {
      if (!active) return;
      const element = select();
      const rect = element?.getBoundingClientRect();
      setUnavailable(!element);
      if (!rect || rect.width < 4 || rect.height < 4) {
        setFrame(null);
        return;
      }
      const nextFrame = {
        top: Math.max(5, rect.top),
        left: Math.max(5, rect.left),
        width: Math.max(4, Math.min(rect.width, window.innerWidth - Math.max(5, rect.left) - 5)),
        height: Math.max(4, Math.min(rect.height, window.innerHeight - Math.max(5, rect.top) - 5)),
      };
      setFrame(old => old && Object.keys(nextFrame).every(k =>
        Math.abs(old[k as keyof Rectangle] - nextFrame[k as keyof Rectangle]) < 1
      ) ? old : nextFrame);
    };
    const onViewportChange = () => {
      window.cancelAnimationFrame(raf);
      raf = window.requestAnimationFrame(measure);
    };
    // Wait for React page navigation and local conditional content to commit.
    timeout = window.setTimeout(() => {
      const element = select();
      element?.scrollIntoView({ behavior: "auto", block: "nearest", inline: "nearest" });
      measure();
    }, currentPage === pageId ? 35 : 120);
    window.addEventListener("resize", onViewportChange);
    window.addEventListener("scroll", onViewportChange, true);
    return () => {
      active = false;
      window.clearTimeout(timeout);
      window.cancelAnimationFrame(raf);
      window.removeEventListener("resize", onViewportChange);
      window.removeEventListener("scroll", onViewportChange, true);
    };
  }, [mode, step.target, step.fallback, pageId, currentPage]);

  const progress = order.reduce((sum, id, i) =>
    sum + (i < currentPageIndex ? discoveryPage(id).steps.length : 0), 0) + stepIndex + 1;
  const total = discoveryPages.reduce((sum, item) => sum + item.steps.length, 0);

  if (mode === "spotlight") {
    // Keep the instruction card OUTSIDE the highlighted real control.
    // The former fixed 212px offset let a longer tooltip obscure its own target.
    const tooltipWidth = Math.min(360, window.innerWidth - 24);
    const tooltipHeight = Math.min(
      tooltipRef.current?.offsetHeight || 315,
      Math.min(340, window.innerHeight - 20),
    );
    const gap = 13;
    const freeBelow = frame ? window.innerHeight - (frame.top + frame.height) - gap : 0;
    const freeAbove = frame ? frame.top - gap : 0;
    const freeLeft = frame ? frame.left - gap : 0;
    const freeRight = frame ? window.innerWidth - frame.left - frame.width - gap : 0;
    const side = frame && Math.max(freeLeft, freeRight) >= tooltipWidth + gap &&
      Math.max(freeAbove, freeBelow) < tooltipHeight + gap;
    const tooltipTop = !frame ? 8 : side
      ? Math.max(8, Math.min(
        frame.top + frame.height / 2 - tooltipHeight / 2,
        window.innerHeight - tooltipHeight - 8,
      ))
      : freeBelow >= tooltipHeight + gap
        ? frame.top + frame.height + gap
        : freeAbove >= tooltipHeight + gap
          ? frame.top - tooltipHeight - gap
          : Math.max(8, Math.min(frame.top - tooltipHeight - gap,
            window.innerHeight - tooltipHeight - 8));
    const tooltipLeft = !frame ? 12 : side
      ? freeRight >= tooltipWidth + gap
        ? frame.left + frame.width + gap
        : frame.left - tooltipWidth - gap
      : Math.max(12, Math.min(
        frame.left + frame.width / 2 - tooltipWidth / 2,
        window.innerWidth - tooltipWidth - 12,
      ));
    const tooltipStyle = frame ? { top: tooltipTop, left: tooltipLeft } : undefined;
    return <div className="discovery-context-layer" data-guide-mode="spotlight">
      {frame ? <div className="discovery-focus-frame" aria-hidden="true"
        style={{ top: frame.top, left: frame.left, width: frame.width, height: frame.height }}/> :
        <div className="discovery-context-dim" aria-hidden="true"/>}
      <div className={"discovery-context-tooltip glass" + (frame ? "" : " discovery-tooltip-centered")}
        ref={tooltipRef} tabIndex={-1}
        role="region" aria-label="Guidage DocuMind" style={tooltipStyle}>
        <div className="discovery-context-top">
          <span><MousePointerClick size={15}/> {page.label} · {stepIndex + 1}/{page.steps.length}</span>
          <button type="button" onClick={onClose} aria-label="Fermer le guide"><X size={17}/></button>
        </div>
        <strong>{step.title}</strong>
        <p>{step.action}</p>
        {unavailable ? <small className="discovery-unavailable">Contrôle absent dans cette instance ou cet état. Aucun clic n'est simulé.</small>
          : <small className="discovery-outcome"><CheckCheck size={13}/>{step.outcome}</small>}
        {step.caution && !demo && !(pageId === "assistant" && aiEnabled) &&
          !(pageId === "documents" && stepIndex === 0 && operator) &&
          <small className="discovery-context-caution">{step.caution}</small>}
        {(demo || pageId === "documents" && !operator || pageId === "assistant" && !aiEnabled) &&
          <small className="discovery-context-caution">
            {demo ? "Démonstration en lecture seule : les actions métier sont désactivées."
              : pageId === "documents" ? "Opération réservée au rôle opérateur."
                : "Assistant IA local indisponible dans cette instance."}
          </small>}
        <div className="discovery-context-actions">
          <button type="button" onClick={() => setMode("lesson")}>Retour au guide</button>
          <button type="button" onClick={next} className="discovery-mini-next">
            {last ? "Terminer" : "Suivant"} <ArrowRight size={14}/>
          </button>
        </div>
      </div>
    </div>;
  }

  return <div className="discovery-layer" data-guide-mode={mode}>
    <button type="button" className="discovery-backdrop"
      aria-label="Fermer Découvrir DocuMind" onClick={onClose}/>
    <section className="discovery-dialog glass" role="dialog" aria-modal="true"
      aria-labelledby="discovery-title" ref={dialogRef} tabIndex={-1}>
      <header className="discovery-header">
        <div className="discovery-header-brand"><span><Fingerprint size={22}/></span>
          <div className="discovery-header-copy">
            <div className="eyebrow"><span className="signal-pulse"/> PRISE EN MAIN · DOCUMIND</div>
            <h2 id="discovery-title">Découvrir <em>DocuMind</em></h2>
            <p>{mode === "home"
              ? "Comprenez votre espace documentaire et apprenez à l'utiliser."
              : "Une action à la fois, sur les vraies pages de l'application."}</p>
          </div>
        </div>
        <button type="button" className="discovery-close icon-button"
          aria-label="Fermer Découvrir DocuMind" onClick={onClose}><X size={19}/></button>
      </header>

      {mode === "home" ? <div className="discovery-home">
        <div className="discovery-home-choices">
          <button className="discovery-choice discovery-choice-primary" type="button"
            onClick={startBeginner}>
            <span className="discovery-choice-icon"><MousePointerClick size={25}/></span>
            <strong>Je débute</strong>
            <small>Commencez par importer un document, puis comprenez ses résultats et ses sources.</small>
            <span className="discovery-choice-action">Commencer <ArrowRight size={16}/></span>
          </button>
          <button className="discovery-choice" type="button"
            onClick={() => choosePage(currentPage)}>
            <span className="discovery-choice-icon"><BookOpenCheck size={25}/></span>
            <strong>Explorer les cinq pages</strong>
            <small>Choisissez un espace et découvrez précisément où cliquer.</small>
            <span className="discovery-choice-action">Choisir une page <ChevronRight size={16}/></span>
          </button>
        </div>
        <div className="discovery-section-title">
          <span>LES CINQ ESPACES</span><small>Choisissez une page pour son mode d'emploi</small>
        </div>
        <div className="discovery-page-cards">
          {discoveryPages.map(item => <button key={item.id}
            type="button" onClick={() => choosePage(item.id)}>
            <PageGlyph page={item.id}/>
            <strong>{item.label}</strong>
            <span>{item.purpose}</span>
          </button>)}
        </div>
        <div className="discovery-flow" aria-label="Parcours documentaire réel">
          <div className="discovery-flow-label">
            <strong>Le circuit d'un document</strong>
            <small>Chaque opération est distincte</small>
          </div>
          <div className="discovery-flow-steps">
            {topics.map((item, idx) => {
              const Icon = item.icon;
              return <span key={item.label} className="discovery-flow-step">
                {idx > 0 && <ChevronRight className="discovery-flow-arrow" size={14}/>}
                <Icon size={17}/><small>{item.label}</small>
              </span>;
            })}
          </div>
          <small className="discovery-flow-warning">Exemple fictif : facture de 120 € validée → montant exploitable ; rejetée → montant exclu. Les opérations restent traçables dans Historique.</small>
        </div>
      </div> : <div className="discovery-lesson">
        <div className="discovery-lesson-nav" aria-label="Guides des cinq pages">
          {discoveryPages.map(item => {
            const Icon = icons[item.id];
            return <button type="button" key={item.id}
              className={pageId === item.id ? "active" : ""}
              aria-pressed={pageId === item.id} onClick={() => choosePage(item.id)}>
              <Icon size={17}/><span>{item.label}</span>
            </button>;
          })}
        </div>
        <div className="discovery-lesson-body" aria-live="polite">
          <div className="discovery-lesson-intro">
            <div><PageGlyph page={pageId}/>
              <span className="discovery-lesson-topic"><strong>{page.label}</strong>
                <small>{page.purpose}</small></span></div>
            <span className="discovery-page-counter">Étape {stepIndex + 1}/{page.steps.length}</span>
          </div>
          <div className="discovery-progress" role="progressbar" aria-label="Progression du guide"
            aria-valuenow={progress} aria-valuemin={0} aria-valuemax={total}>
            <span style={{width: `${progress / total * 100}%`}}/>
          </div>
          <div className="discovery-lesson-card">
            <div className="discovery-step-marker"><span>{stepIndex + 1}</span><MousePointerClick size={26}/></div>
            <div className="discovery-step-copy">
              <span className="eyebrow">OÙ CLIQUER · QUOI FAIRE</span>
              <h3>{step.title}</h3>
              <p>{step.action}</p>
            </div>
          </div>
          <div className="discovery-step-outcome">
            <CheckCheck size={18}/>
            <div><strong>Résultat attendu</strong><p>{step.outcome}</p></div>
          </div>
          {step.caution && <div className="discovery-step-note"><ShieldCheck size={16}/>{step.caution}</div>}
          <GuidanceRestriction page={pageId} demo={demo} operator={operator} aiEnabled={aiEnabled}/>
        </div>
      </div>}

      <footer className="discovery-footer">
        {mode === "home" ? <>
          <span className="discovery-footer-safe"><ShieldCheck size={15}/>
            Guide uniquement : aucune action automatique sur vos documents.</span>
          <button type="button" className="btn btn-primary" onClick={startBeginner}>
            Commencer <ArrowRight size={16}/>
          </button>
        </> : <>
          <button type="button" className="btn btn-ghost" onClick={previous}>
            <ArrowLeft size={16}/> Précédent
          </button>
          <span className="discovery-step-count">{progress}/{total} étapes</span>
          <button type="button" className="btn btn-secondary" onClick={showInApp}>
            <MousePointerClick size={16}/> Voir dans l'application
          </button>
          <button type="button" className="btn btn-primary" onClick={next}>
            {last ? "Terminer" : "Suivant"} <ArrowRight size={16}/>
          </button>
        </>}
      </footer>
    </section>
  </div>;
}
