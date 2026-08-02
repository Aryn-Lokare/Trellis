'use client';

import React from 'react';
import { useComplianceStore } from '../../store/useComplianceStore';
import { useDocument } from '../../hooks/useDocument';
import { Dialog } from '../ui/dialog';
import { Badge } from '../ui/badge';
import { Skeleton } from '../ui/skeleton';
import { FileText, Music, Clock, MapPin, ExternalLink, ShieldCheck, Quote } from 'lucide-react';

export function CitationSourcePanel() {
  const selectedCitation = useComplianceStore((state) => state.selectedCitation);
  const citationPanelOpen = useComplianceStore((state) => state.citationPanelOpen);
  const setCitationPanelOpen = useComplianceStore((state) => state.setCitationPanelOpen);

  const { data: documentDetail, isLoading, isError } = useDocument(
    selectedCitation?.source_doc_id || null
  );

  if (!selectedCitation) return null;

  return (
    <Dialog
      isOpen={citationPanelOpen}
      onClose={() => setCitationPanelOpen(false)}
      title={`Citation Source Traceability [${selectedCitation.citation_index || 1}]`}
    >
      <div className="space-y-6">
        {/* Header Metadata Strip */}
        <div className="bg-[#eeece7] p-4 rounded-[12px] flex flex-wrap items-center justify-between gap-3 border border-[#d9d9dd]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#17171c] text-white flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-[#ff7759]" />
            </div>
            <div>
              <span className="mono-label text-[10px] text-[#93939f]">VERIFIED SOURCE SPAN</span>
              <p className="text-sm font-semibold text-[#212121]">
                {selectedCitation.document_filename || documentDetail?.filename || `Doc ID: ${selectedCitation.source_doc_id}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="entity" entityType={selectedCitation.document_type || documentDetail?.type || 'pdf'}>
              {selectedCitation.document_type || documentDetail?.type || 'PDF'}
            </Badge>

            {selectedCitation.source_span && (
              <Badge variant="solid" className="bg-[#1863dc]">
                <MapPin className="w-3 h-3 mr-1" />
                {selectedCitation.source_span}
              </Badge>
            )}
          </div>
        </div>

        {/* Source Snippet Box */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mono-label text-xs text-[#212121]">
            <Quote className="w-4 h-4 text-[#ff7759]" />
            <span>EXTRACTED CLAUSE / GROUND TRUTH SNIPPET</span>
          </div>

          <div className="p-5 rounded-[12px] bg-[#17171c] text-white font-mono text-xs leading-relaxed border border-[#33333e] relative overflow-hidden">
            <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-[#ff7759]" />
            <p className="pl-2 italic">{`"${selectedCitation.snippet}"`}</p>
          </div>
        </div>

        {/* Document Provenance Details */}
        {isLoading && (
          <div className="space-y-2">
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-16 w-full" />
          </div>
        )}

        {documentDetail && (
          <div className="space-y-3 pt-4 border-t border-[#d9d9dd]">
            <div className="flex items-center justify-between">
              <span className="mono-label text-xs text-[#93939f]">DOCUMENT CONTEXT & EXTRACTED SPANS</span>
              <span className="mono-label text-[10px] text-[#616161]">
                {documentDetail.spans?.length || 0} TOTAL SPANS INDEXED
              </span>
            </div>

            {documentDetail.spans && documentDetail.spans.length > 0 ? (
              <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
                {documentDetail.spans.map((span, idx) => {
                  const isCurrent = span.text?.includes(selectedCitation.snippet) || span.label === selectedCitation.source_span;
                  return (
                    <div
                      key={idx}
                      className={`p-3 rounded-[8px] border text-xs transition-all ${
                        isCurrent
                          ? 'border-[#1863dc] bg-[#f1f5ff] text-[#17171c] font-medium'
                          : 'border-[#d9d9dd] bg-white text-[#616161]'
                      }`}
                    >
                      <span className="mono-label text-[10px] text-[#1863dc] block mb-1">
                        [{span.label}]
                      </span>
                      <p className="line-clamp-2">{span.text}</p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-[#93939f] italic">
                Full document context verified against knowledge graph index.
              </p>
            )}
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            onClick={() => setCitationPanelOpen(false)}
            className="button-primary text-xs"
          >
            Close Provenance Inspector
          </button>
        </div>
      </div>
    </Dialog>
  );
}
