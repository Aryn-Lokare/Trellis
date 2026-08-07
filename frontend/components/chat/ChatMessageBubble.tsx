'use client';

import React from 'react';
import { QueryResponse, Citation } from '../../types';
import { InlineCitationText } from './InlineCitationText';
import { MiniSubgraphView } from './MiniSubgraphView';
import {
  Bot,
  User,
  ShieldCheck,
  FileCheck2,
  FileText,
  Volume2,
  Table,
  Network,
  Database,
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface ChatMessageBubbleProps {
  question: string;
  response: QueryResponse;
}

export function ChatMessageBubble({ question, response }: ChatMessageBubbleProps) {
  // Helper to determine icon by file type/extension
  const getFileIcon = (filename?: string) => {
    if (!filename) return FileText;
    const name = filename.toLowerCase();
    if (name.endsWith('.pdf')) return FileText;
    if (
      name.endsWith('.wav') ||
      name.endsWith('.mp3') ||
      name.includes('audio') ||
      name.includes('call')
    )
      return Volume2;
    if (
      name.endsWith('.csv') ||
      name.endsWith('.xlsx') ||
      name.includes('table') ||
      name.includes('spreadsheet')
    )
      return Table;
    if (
      name.endsWith('.svg') ||
      name.endsWith('.png') ||
      name.includes('diagram') ||
      name.includes('schematic')
    )
      return Network;
    return FileText;
  };

  // Helper to determine color by file type
  const getFileColor = (filename?: string) => {
    if (!filename) return 'text-[#ff7759]';
    const name = filename.toLowerCase();
    if (name.endsWith('.pdf')) return 'text-[#1863dc]'; // Action Blue
    if (name.endsWith('.wav') || name.endsWith('.mp3') || name.includes('audio'))
      return 'text-[#ff7759]'; // Coral
    if (name.endsWith('.csv') || name.endsWith('.xlsx') || name.includes('table'))
      return 'text-[#10b981]'; // Emerald/Green
    if (name.endsWith('.svg') || name.endsWith('.png') || name.includes('diagram'))
      return 'text-[#9b60aa]'; // Purple
    return 'text-white';
  };

  const f1 = response.f1_score ?? 1.0;
  const hallucinationRate =
    !response.citations || response.citations.length === 0
      ? 0
      : Math.max(0, Math.min(100, Math.round((1.0 - f1) * 100)));

  // F1 diagnostic score styling
  const getF1Style = (score: number) => {
    if (score >= 0.9) return 'text-[#10b981] border-[#10b981]/20 bg-[#10b981]/5';
    if (score >= 0.7) return 'text-amber-400 border-amber-500/20 bg-amber-500/5';
    return 'text-rose-400 border-rose-500/20 bg-rose-500/5';
  };

  const getHallucinationStyle = (rate: number) => {
    if (rate === 0) return 'text-[#10b981] border-[#10b981]/20 bg-[#10b981]/5';
    if (rate <= 30) return 'text-amber-400 border-amber-500/20 bg-amber-500/5';
    return 'text-rose-400 border-rose-500/20 bg-rose-500/5';
  };

  // Extract unique documents cited
  const uniqueDocs = response.citations
    ? Array.from(
        new Map(
          response.citations.map((c) => [c.source_doc_id || c.document_filename, c])
        ).values()
      )
    : [];

  return (
    <div className="space-y-6">
      {/* User Question Bubble */}
      <div className="flex items-start justify-end gap-3">
        <div className="max-w-2xl bg-[#eeece7] text-[#212121] p-4 rounded-[16px] border border-[#d9d9dd] shadow-sm">
          <span className="mono-label text-[10px] text-[#93939f] block mb-1">
            COMPLIANCE OFFICER QUERY
          </span>
          <p className="text-sm font-medium font-sans leading-relaxed">{question}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-[#17171c] text-white flex items-center justify-center shrink-0 shadow-sm">
          <User className="w-4 h-4" />
        </div>
      </div>

      {/* Agent Response Console Card */}
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-[#ff7759] text-white flex items-center justify-center shrink-0 mt-1 shadow-sm">
          <Bot className="w-4 h-4" />
        </div>

        <div className="flex-1 max-w-4xl bg-[#17171c] text-white rounded-[22px] p-6 sm:p-8 space-y-6 border border-white/5 shadow-xl relative overflow-hidden">
          {/* Subtle radial glow overlay */}
          <div className="absolute -top-24 -right-24 w-48 h-48 bg-[#003c33]/25 rounded-full blur-3xl pointer-events-none" />

          {/* Header */}
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-[#ff7759]" />
              <span className="font-semibold tracking-tight text-sm font-display text-white">
                GRAPHRAG SYNTHESIZED VERDICT
              </span>
            </div>
            <span className="mono-label text-[9px] text-white/50 bg-white/5 border border-white/10 px-2.5 py-1 rounded">
              SECURE INFERENCE
            </span>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pb-2">
            {/* F1 Score Card */}
            <div
              className={cn(
                'border rounded-xl p-4 flex flex-col justify-between shadow-sm transition-all',
                getF1Style(f1)
              )}
            >
              <div>
                <span className="mono-label text-[10px] text-white/55 tracking-wider font-bold block">
                  ENTITY-RELATION F1 SCORE
                </span>
                <div className="flex items-baseline gap-1 mt-1.5">
                  <span className="text-3xl font-mono font-bold text-white">
                    {f1.toFixed(2)}
                  </span>
                  <span className="text-xs text-white/70">F1</span>
                </div>
              </div>
              <p className="text-[10.5px] text-white/50 mt-3 leading-normal font-sans">
                Measures how accurately the answer's claims correspond to the retrieved compliance
                graph.
              </p>
            </div>

            {/* Hallucination Rate Card */}
            <div
              className={cn(
                'border rounded-xl p-4 flex flex-col justify-between shadow-sm transition-all',
                getHallucinationStyle(hallucinationRate)
              )}
            >
              <div>
                <span className="mono-label text-[10px] text-white/55 tracking-wider font-bold block">
                  DETECTED HALLUCINATION RATE
                </span>
                <div className="flex items-baseline gap-1 mt-1.5">
                  <span className="text-3xl font-mono font-bold text-white">
                    {hallucinationRate}%
                  </span>
                </div>
              </div>
              <p className="text-[10.5px] text-white/50 mt-3 leading-normal font-sans">
                Indicates the percentage of cited facts not verified in the retrieved knowledge
                context.
              </p>
            </div>
          </div>

          {/* Complete Synthesized Answer Text */}
          <div className="space-y-2 pt-2">
            <span className="mono-label text-[10px] text-white/50 block font-bold tracking-wider">
              COMPLETE VERDICT ANSWER:
            </span>
            <div className="text-[15px] leading-relaxed text-white/95 font-sans border-l-2 border-[#ff7759]/40 pl-4 py-1">
              <InlineCitationText text={response.answer} citations={response.citations || []} />
            </div>
          </div>

          {/* Sources Contributing */}
          {uniqueDocs.length > 0 && (
            <div className="space-y-3 pt-2">
              <span className="mono-label text-[10px] text-white/50 block font-bold tracking-wider">
                SOURCES THE INFORMATION WAS EXTRACTED FROM ({uniqueDocs.length}):
              </span>
              <div className="flex flex-wrap gap-2.5">
                {uniqueDocs.map((c, idx) => {
                  const FileIcon = getFileIcon(c.document_filename);
                  const fileColor = getFileColor(c.document_filename);
                  return (
                    <div
                      key={c.source_doc_id || idx}
                      className="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full pl-2 pr-3.5 py-1 text-xs text-white shadow-sm hover:bg-white/10 transition-colors"
                    >
                      <div className={cn('p-1 rounded-full bg-white/5', fileColor)}>
                        <FileIcon className="w-3.5 h-3.5" />
                      </div>
                      <span className="font-medium truncate max-w-[220px]">
                        {c.document_filename || `Document-${c.source_doc_id?.slice(0, 6)}`}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Detailed Citations Excerpts */}
          {response.citations && response.citations.length > 0 && (
            <div className="space-y-4 pt-4 border-t border-white/10">
              <div className="flex items-center gap-2.5">
                <FileCheck2 className="w-4.5 h-4.5 text-[#ff7759]" />
                <span className="font-semibold tracking-tight text-sm font-display text-white">
                  DETAILED CITATIONS TRACEABILITY ({response.citations.length})
                </span>
              </div>

              <div className="space-y-3.5 max-h-[350px] overflow-y-auto pr-1.5 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                {response.citations.map((c, idx) => {
                  const FileIcon = getFileIcon(c.document_filename);
                  const fileColor = getFileColor(c.document_filename);
                  const isVerified = c.verified !== false; // defaults to true if not explicitly set to false

                  return (
                    <div
                      key={c.id || idx}
                      className="p-4 rounded-[16px] bg-black/30 border border-white/5 space-y-3 shadow-md hover:border-white/10 transition-all duration-200"
                    >
                      {/* Citation Header */}
                      <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
                        <div className="flex items-center gap-2">
                          <span className="mono-label text-[10px] font-bold text-[#ffad9b] font-mono bg-[#ff7759]/10 border border-[#ff7759]/20 px-2 py-0.5 rounded">
                            {c.source_span}
                          </span>
                          <div className="flex items-center gap-1.5 text-white/70">
                            <FileIcon className={cn('w-3.5 h-3.5', fileColor)} />
                            <span className="font-medium truncate max-w-[200px]">
                              {c.document_filename || `Document-${c.source_doc_id?.slice(0, 6)}`}
                            </span>
                          </div>
                        </div>

                        {/* Verification Status Badge */}
                        <span
                          className={cn(
                            'px-2.5 py-0.5 rounded-full text-[9px] font-bold border',
                            !isVerified
                              ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          )}
                        >
                          {!isVerified ? 'UNVERIFIED CLAIM' : 'VERIFIED MATCH'}
                        </span>
                      </div>

                      {/* Excerpt Snippet */}
                      {c.snippet ? (
                        <div className="text-xs text-white/80 bg-white/5 border border-white/5 rounded-lg p-3 italic leading-relaxed font-sans">
                          &ldquo;{c.snippet}&rdquo;
                        </div>
                      ) : (
                        <div className="text-xs text-rose-400 bg-rose-950/10 border border-rose-950/20 rounded-lg p-3 leading-relaxed font-sans">
                          This citation details facts or statements that could not be validated in
                          the traversed compliance subgraph.
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Embedded Subgraph Panel */}
          {response.subgraph && (
            <div className="pt-2 border-t border-white/10">
              <MiniSubgraphView subgraph={response.subgraph} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}