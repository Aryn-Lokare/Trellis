'use client';

import React from 'react';
import { useComplianceStore } from '../../store/useComplianceStore';
import { Citation } from '../../types';
import { FileText, Music, Clock, Layers } from 'lucide-react';

interface CitationChipProps {
  citation: Citation;
}

export function CitationChip({ citation }: CitationChipProps) {
  const setSelectedCitation = useComplianceStore((state) => state.setSelectedCitation);

  return (
    <button
      onClick={() => setSelectedCitation(citation)}
      className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded-[4px] bg-[#1863dc]/10 text-[#1863dc] hover:bg-[#1863dc] hover:text-white border border-[#1863dc]/30 font-mono text-xs font-semibold transition-all cursor-pointer transform hover:scale-105 align-baseline"
      title={`Trace Source: ${citation.source_span || 'View Citation'}`}
    >
      <span>[{citation.citation_index || 1}]</span>
      {citation.source_span && (
        <span className="text-[10px] opacity-80 font-mono underline decoration-dotted">
          {citation.source_span}
        </span>
      )}
    </button>
  );
}
