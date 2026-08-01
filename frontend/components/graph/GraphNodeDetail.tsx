'use client';

import React from 'react';
import { useComplianceStore } from '../../store/useComplianceStore';
import { Badge } from '../ui/badge';
import { X, MapPin, FileText, Share2, Info, ArrowRight } from 'lucide-react';
import { useComplianceStore as useStore } from '../../store/useComplianceStore';
import { Citation } from '../../types';

export function GraphNodeDetail() {
  const selectedNode = useComplianceStore((state) => state.selectedNode);
  const selectedEdge = useComplianceStore((state) => state.selectedEdge);
  const clearSelection = useComplianceStore((state) => state.clearSelection);
  const setSelectedCitation = useComplianceStore((state) => state.setSelectedCitation);

  if (!selectedNode && !selectedEdge) return null;

  const handleTraceCitation = () => {
    const item = selectedNode || selectedEdge;
    if (!item) return;

    const citation: Citation = {
      id: `cit-${item.id}`,
      citation_index: 1,
      source_doc_id: item.source_doc_id || 'unknown',
      source_span: item.source_span || 'N/A',
      snippet: selectedNode
        ? `Knowledge Graph Entity: ${selectedNode.name} (${selectedNode.type})`
        : `Relationship Path: ${selectedEdge?.relationship_type}`,
    };
    setSelectedCitation(citation);
  };

  return (
    <div className="bg-[#17171c] text-white rounded-[22px] p-6 border border-[#212121] space-y-5 animate-in slide-in-from-right duration-200">
      <div className="flex items-center justify-between border-b border-[#33333e] pb-3">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-[#ff7759]" />
          <span className="mono-label text-white">
            {selectedNode ? 'ENTITY PROVENANCE INSPECTOR' : 'RELATIONSHIP PATH INSPECTOR'}
          </span>
        </div>
        <button
          onClick={clearSelection}
          className="p-1 text-[#93939f] hover:text-white rounded-full transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Selected Entity Details */}
      {selectedNode && (
        <div className="space-y-4">
          <div>
            <span className="mono-label text-[10px] text-[#93939f]">ENTITY NAME & TAXONOMY</span>
            <h3 className="text-xl font-medium text-white mt-0.5">{selectedNode.name}</h3>
            <div className="mt-2">
              <Badge variant="entity" entityType={selectedNode.type}>
                {selectedNode.type}
              </Badge>
            </div>
          </div>

          <div className="bg-[#22222c] p-4 rounded-[12px] border border-[#33333e] space-y-2 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-[#93939f]">SOURCE DOC ID:</span>
              <span className="text-[#ffad9b] font-bold">{selectedNode.source_doc_id || 'N/A'}</span>
            </div>
            <div className="flex justify-between border-t border-[#33333e] pt-2">
              <span className="text-[#93939f]">EXACT SOURCE SPAN:</span>
              <span className="text-[#1863dc] font-bold flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {selectedNode.source_span || 'Page N/A'}
              </span>
            </div>
          </div>

          <button
            onClick={handleTraceCitation}
            className="w-full button-primary text-xs justify-center"
          >
            Trace Source Document Span
          </button>
        </div>
      )}

      {/* Selected Relationship Path Details */}
      {selectedEdge && (
        <div className="space-y-4">
          <div>
            <span className="mono-label text-[10px] text-[#93939f]">RELATIONSHIP TYPE</span>
            <h3 className="text-lg font-mono text-[#ff7759] mt-0.5 uppercase font-bold">
              {selectedEdge.relationship_type}
            </h3>
          </div>

          <div className="bg-[#22222c] p-4 rounded-[12px] border border-[#33333e] space-y-2 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-[#93939f]">SOURCE DOC ID:</span>
              <span className="text-[#ffad9b] font-bold">{selectedEdge.source_doc_id || 'N/A'}</span>
            </div>
            <div className="flex justify-between border-t border-[#33333e] pt-2">
              <span className="text-[#93939f]">EXACT SOURCE SPAN:</span>
              <span className="text-[#1863dc] font-bold flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {selectedEdge.source_span || 'Page N/A'}
              </span>
            </div>
          </div>

          <button
            onClick={handleTraceCitation}
            className="w-full button-primary text-xs justify-center"
          >
            Trace Source Document Span
          </button>
        </div>
      )}
    </div>
  );
}
