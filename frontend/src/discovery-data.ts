import type { Tab } from "./types";

/**
 * Interface help describes existing controls, not a simulated run of the
 * import, D2 validation or RAG pipeline.
 */
export type GuideStep = {
  title: string;
  action: string;
  outcome: string;
  target: string;
  fallback?: string;
  caution?: string;
};

export type GuidePage = {
  id: Tab;
  label: string;
  short: string;
  purpose: string;
  steps: readonly GuideStep[];
};

export const discoveryPages: readonly GuidePage[] = [
  {
    id: "overview",
    label: "Vue d'ensemble",
    short: "Comprendre",
    purpose: "Voir en un instant les documents suivis et les montants réellement vérifiés.",
    steps: [
      {
        title: "Lire les quatre indicateurs",
        action: "Repérez les documents suivis, validés ou indexés, le TTC vérifié et les documents rejetés.",
        outcome: "Vous distinguez les fichiers enregistrés des montants issus de factures acceptées.",
        target: ".overview-hero-kpis",
      },
      {
        title: "Comprendre les graphiques",
        action: "Consultez « Évolution des dépenses » et « Contrôle documentaire ».",
        outcome: "Les montants proviennent des factures validées ; les documents rejetés sont exclus.",
        target: ".overview-main-grid",
      },
      {
        title: "Accéder à un document",
        action: "Cliquez sur « Explorer les documents » pour ouvrir la bibliothèque.",
        outcome: "Vous arrivez dans Documents, où vous pourrez importer ou examiner un fichier.",
        target: ".overview-hero .hero-actions .btn-primary",
      },
    ],
  },
  {
    id: "documents",
    label: "Documents",
    short: "Importer",
    purpose: "Importer un fichier, contrôler ses données et consulter sa provenance.",
    steps: [
      {
        title: "Choisir un fichier",
        action: "Cliquez sur « Choisir un fichier », puis sélectionnez un PDF textuel, CSV ou XLSX (5 Mio maximum).",
        outcome: "Le nom du fichier sélectionné s'affiche avant l'envoi.",
        caution: "L'import nécessite une session locale avec le rôle opérateur.",
        target: ".documents-upload-picker",
        fallback: ".documents-upload-box",
      },
      {
        title: "Lancer l'import",
        action: "Cliquez sur « Importer » après avoir sélectionné votre fichier.",
        outcome: "Le fichier rejoint le catalogue. Il n'est pas encore automatiquement validé.",
        target: ".documents-upload-submit",
      },
      {
        title: "Ouvrir la fiche documentaire",
        action: "Dans le « Catalogue », choisissez une ligne ou sa flèche de détails.",
        outcome: "La fiche montre son état, ses extraits, ses anomalies et son historique lorsqu'ils existent.",
        target: ".document-table-pane",
      },
      {
        title: "Traiter puis indexer si possible",
        action: "Pour un document reçu, lancez « Traiter avec D2 » dans sa fiche. Après acceptation, vous pouvez lancer « Indexer pour l'IA » si l'IA locale est active.",
        outcome: "Le traitement contrôle les données ; l'indexation rend les passages acceptés interrogeables.",
        caution: "Ces actions sont distinctes. Un document rejeté n'alimente pas les indicateurs et ne peut pas être indexé.",
        target: ".documents-preview-layer .drawer-actions",
        fallback: ".documents-cockpit",
      },
    ],
  },
  {
    id: "analytics",
    label: "Analyse & KPI",
    short: "Analyser",
    purpose: "Consulter les résultats SQL calculés à partir des factures acceptées.",
    steps: [
      {
        title: "Comprendre les quatre KPI",
        action: "Lisez les factures acceptées, le TTC en EUR, le nombre de fournisseurs et le taux de rejet.",
        outcome: "Vous distinguez les montants de factures validées du taux de rejet des documents.",
        target: ".analytics-premium-kpis",
        fallback: ".analytics-premium-hero",
      },
      {
        title: "Lire dépenses et qualité",
        action: "Comparez les dépenses dans le temps, par fournisseur, puis la répartition des états documentaires.",
        outcome: "Les graphiques disponibles utilisent les données SQL existantes, sans additionner les devises.",
        target: ".analytics-grid",
        fallback: ".analytics-unavailable",
      },
      {
        title: "Examiner devises et anomalies",
        action: "Dans les deux modules inférieurs, consultez « Réconciliation par devise » et « Anomalies détectées ».",
        outcome: "Vous repérez les incohérences et vérifiez les montants dans chaque devise séparément.",
        target: ".analytics-bottom-grid",
        fallback: ".analytics-unavailable",
      },
    ],
  },
  {
    id: "assistant",
    label: "Assistant IA",
    short: "Interroger",
    purpose: "Poser une question et vérifier les citations de documents indexés.",
    steps: [
      {
        title: "Préparer une question",
        action: "Choisissez un « Exemple de demande » : il remplit le champ sans envoyer la question.",
        outcome: "Vous pouvez modifier le texte avant toute recherche.",
        caution: "L'Assistant IA nécessite l'instance locale avec Ollama et des passages indexés.",
        target: ".assistant-request-grid",
      },
      {
        title: "Envoyer à l'assistant",
        action: "Écrivez votre question dans le champ, puis utilisez la flèche d'envoi (ou Entrée).",
        outcome: "La recherche RAG s'exécute uniquement si l'IA locale est disponible.",
        target: ".assistant-form",
      },
      {
        title: "Vérifier la réponse",
        action: "Lisez la réponse et ouvrez ses citations lorsqu'elles sont fournies.",
        outcome: "Chaque citation renvoie à un document et à un passage ; si les preuves manquent, l'assistant peut s'abstenir.",
        target: ".assistant-conversation",
        caution: "Une réponse IA peut être incorrecte : contrôlez les extraits avant une décision.",
      },
    ],
  },
  {
    id: "activity",
    label: "Historique",
    short: "Retrouver",
    purpose: "Retrouver les opérations, leurs dates, leurs acteurs et leurs documents.",
    steps: [
      {
        title: "Rechercher une opération",
        action: "Saisissez un nom de document, une action ou un acteur dans « Action, document, acteur… ».",
        outcome: "Le journal filtre les événements actuellement chargés.",
        caution: "La recherche locale ne parcourt pas nécessairement tout l'historique PostgreSQL.",
        target: ".activity-toolbar .search-field",
        fallback: ".activity-premium-journal",
      },
      {
        title: "Consulter l'événement et sa source",
        action: "Lisez l'action, la date et l'acteur, puis cliquez sur un événement pour ouvrir son document.",
        outcome: "Vous pouvez consulter la fiche du document concerné, lorsqu'elle est disponible.",
        target: ".activity-timeline-scroll",
        fallback: ".activity-premium-journal",
      },
    ],
  },
];

export function discoveryPage(id: Tab): GuidePage {
  const page = discoveryPages.find(item => item.id === id);
  if (!page) throw new Error(`Page DocuMind inconnue : ${id}`);
  return page;
}

export const discoveryRoute: readonly Tab[] =
  ["overview", "documents", "analytics", "assistant", "activity"];

// First-time use starts with the first actionable workflow, not empty KPIs.
export const beginnerRoute: readonly Tab[] =
  ["documents", "overview", "analytics", "assistant", "activity"];
