'use client';

import React from 'react';
import { QueryResponse } from '../../types';
import { InlineCitationText } from './InlineCitationText';
import { MiniSubgraphView } from './MiniSubgraphView';
import { CitationChip } from '../citations/CitationChip';
import { Bot, User, ShieldCheck, FileCheck2 } from 'lucide-react';

interface ChatMessageBubbleProps {
  question: string;
  response: QueryResponse;
}

export function ChatMessageBubble({ question, response }: ChatMessageBubbleProps) {
  return (
    <div className="space-y-6">
      {/* User Question Bubble */}
      <div className="flex items-start justify-end gap-3">
        <div className="max-w-2xl bg-[#eeece7] text-[#212121] p-4 rounded-[16px] border border-[#d9d9dd]">
          <span className="mono-label text-[10px] text-[#93939f] block mb-1">
            COMPLIANCE OFFICER QUERY
          </span>
          <p className="text-base font-medium">{question}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-[#1863dc] text-white flex items-center justify-center shrink-0">
          <User className="w-4 h-4" />
        </div>
      </div>

      {/* Agent Response Console Card */}
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-[#ff7759] text-white flex items-center justify-center shrink-0 mt-1">
          <Bot className="w-4 h-4" />
        </div>

        <div className="flex-1 max-w-4xl bg-[#17171c] text-white rounded-[22px] p-6 sm:p-8 space-y-6 border border-[#212121]">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#33333e] pb-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-[#ff7759]" />
              <span className="mono-label text-white">GRAPHRAG SYNTHESIZED VERDICT</span>
            </div>
            <span className="mono-label text-[10px] text-[#93939f] bg-[#22222c] px-2.5 py-1 rounded">
              CITATIONS VERIFIED ({response.citations?.length || 0})
            </span>
          </div>

          {/* Synthesized Cited Answer Text */}
          <div className="text-white space-y-4">
            <InlineCitationText text={response.answer} citations={response.citations || []} />
          </div>

          {/* Citations List Box */}
          {response.citations && response.citations.length > 0 && (
            <div className="bg-[#22222c] rounded-[12px] p-4 border border-[#33333e] space-y-3">
              <div className="flex items-center gap-2 mono-label text-xs text-[#ffad9b]">
                <FileCheck2 className="w-4 h-4 text-[#ff7759]" />
                <span>GROUND TRUTH CITATION SOURCES (CLICK TO TRACE):</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {response.citations.map((c) => (
                  <div
                    key={c.id}
                    className="p-2.5 rounded-[8px] bg-[#17171c] border border-[#33333e] flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <CitationChip citation={c} />
                      <span className="text-white truncate font-medium">
                        {c.document_filename || `Doc ${c.source_doc_id.slice(0, 6)}`}
                      </span>
                    </div>
                    <span className="mono-label text-[10px] text-[#ffad9b] shrink-0">
                      {c.source_span}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Embedded Subgraph Panel */}
          {response.subgraph && <MiniSubgraphView subgraph={response.subgraph} />}
        </div>
      </div>
    </div>
  );
}
