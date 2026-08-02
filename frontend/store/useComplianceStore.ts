import { create } from 'zustand';
import { Citation, Entity, Relationship, Subgraph } from '../types';

interface ComplianceState {
  // Selected citation for source panel inspection
  selectedCitation: Citation | null;
  citationPanelOpen: boolean;
  
  // Active query subgraph
  activeSubgraph: Subgraph | null;

  // Selected node or edge in graph visualization
  selectedNode: Entity | null;
  selectedEdge: Relationship | null;

  // Search / Deep link context
  activeQuestion: string;

  // Actions
  setSelectedCitation: (citation: Citation | null) => void;
  setCitationPanelOpen: (open: boolean) => void;
  setActiveSubgraph: (subgraph: Subgraph | null) => void;
  setSelectedNode: (node: Entity | null) => void;
  setSelectedEdge: (edge: Relationship | null) => void;
  setActiveQuestion: (question: string) => void;
  clearSelection: () => void;
}

export const useComplianceStore = create<ComplianceState>((set) => ({
  selectedCitation: null,
  citationPanelOpen: false,
  activeSubgraph: null,
  selectedNode: null,
  selectedEdge: null,
  activeQuestion: '',

  setSelectedCitation: (citation) =>
    set({
      selectedCitation: citation,
      citationPanelOpen: !!citation,
    }),

  setCitationPanelOpen: (open) =>
    set((state) => ({
      citationPanelOpen: open,
      selectedCitation: open ? state.selectedCitation : null,
    })),

  setActiveSubgraph: (subgraph) => set({ activeSubgraph: subgraph }),

  setSelectedNode: (node) =>
    set({
      selectedNode: node,
      selectedEdge: null,
    }),

  setSelectedEdge: (edge) =>
    set({
      selectedEdge: edge,
      selectedNode: null,
    }),

  setActiveQuestion: (question) => set({ activeQuestion: question }),

  clearSelection: () =>
    set({
      selectedCitation: null,
      citationPanelOpen: false,
      selectedNode: null,
      selectedEdge: null,
    }),
}));
