'use client';

import React from 'react';
import { QueryResponse, Citation } from '../../types';
import { InlineCitationText } from './InlineCitationText';
import { MiniSubgraphView } from './MiniSubgraphView';
import { CitationChip } from '../citations/CitationChip';
import { 
  Bot, 
  User, 
  ShieldCheck, 
  FileCheck2, 
  FileText, 
  Volume2, 
  Table, 
  Network,
  Cpu,
  ArrowRight
} from 'lucide-react';

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
    if (name.endsWith('.wav') || name.endsWith('.mp3') || name.includes('audio') || name.includes('call')) return Volume2;
    if (name.endsWith('.csv') || name.endsWith('.xlsx') || name.includes('table') || name.includes('spreadsheet')) return Table;
    if (name.endsWith('.svg') || name.endsWith('.png') || name.includes('diagram') || name.includes('schematic')) return Network;
    return FileText;
  };

  // Helper to determine color by file type
  const getFileColor = (filename?: string) => {
    if (!filename) return 'text-[#ff7759]';
    const name = filename.toLowerCase();
    if (name.endsWith('.pdf')) return 'text-[#1863dc]'; // Action Blue
    if (name.endsWith('.wav') || name.endsWith('.mp3') || name.includes('audio')) return 'text-[#ff7759]'; // Coral
    if (name.endsWith('.csv') || name.endsWith('.xlsx') || name.includes('table')) return 'text-[#10b981]'; // Emerald/Green
    if (name.endsWith('.svg') || name.endsWith('.png') || name.includes('diagram')) return 'text-[#9b60aa]'; // Purple
    return 'text-white';
  };

  const f1 = response.f1_score ?? 1.0;
  
  // F1 diagnostic score styling
  const getF1Style = (score: number) => {
    if (score >= 0.9) return 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30';
    if (score >= 0.7) return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  };

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
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-white/10 pb-4 gap-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-[#ff7759]" />
              <span className="font-semibold tracking-tight text-sm font-display text-white">
                GRAPHRAG SYNTHESIZED VERDICT
              </span>
            </div>
            
            <div className="flex items-center gap-2">
              {/* F1 diagnostic tag */}
              <span className={`px-2.5 py-1 rounded text-[10px] font-mono border ${getF1Style(f1)}`}>
                DIAGNOSTIC SCORE: {f1.toFixed(2)} F1
              </span>
              
              <span className="mono-label text-[9px] text-white/70 bg-white/5 border border-white/10 px-2.5 py-1 rounded">
                CITATIONS VERIFIED ({response.citations?.length || 0})
              </span>
            </div>
          </div>

          {/* Synthesized Cited Answer Text */}
          <div className="text-[15px] leading-relaxed text-white/90 font-sans border-l-2 border-[#ff7759]/40 pl-4 py-1">
            <InlineCitationText text={response.answer} citations={response.citations || []} />
          </div>

          {/* Citations List Box */}
          {response.citations && response.citations.length > 0 && (
            <div className="bg-white/5 rounded-2xl p-5 border border-white/10 space-y-4">
              <div className="flex items-center gap-2 mono-label text-[11px] tracking-wider text-white/80">
                <FileCheck2 className="w-4.5 h-4.5 text-[#ff7759]" />
                <span>GROUND TRUTH CITATION SOURCES (CLICK TO TRACE):</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {response.citations.map((c) => {
                  const FileIcon = getFileIcon(c.document_filename);
                  const fileColor = getFileColor(c.document_filename);
                  return (
                    <div
                      key={c.id}
                      className="p-3.5 rounded-xl bg-black/35 hover:bg-black/50 border border-white/5 hover:border-white/15 transition-all duration-200 flex items-center justify-between text-xs cursor-pointer group"
                    >
                      <div className="flex items-center gap-2.5 truncate min-w-0">
                        <div className={`p-1.5 rounded-lg bg-white/5 group-hover:bg-white/10 transition-colors ${fileColor}`}>
                          <FileIcon className="w-4 h-4" />
                        </div>
                        <div className="flex flex-col truncate min-w-0">
                          <span className="text-white truncate font-medium group-hover:text-[#ff7759] transition-colors">
                            {c.document_filename || `Doc ${c.source_doc_id.slice(0, 6)}`}
                          </span>
                          <span className="text-[10px] text-[#93939f] font-mono mt-0.5">
                            {c.document_type ? c.document_type.toUpperCase() : 'DOCUMENT'} SOURCE
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0 ml-2">
                        <span className="mono-label text-[10px] font-bold text-[#ffad9b] font-mono bg-[#ff7759]/10 border border-[#ff7759]/20 px-2 py-0.5 rounded">
                          {c.source_span}
                        </span>
                      </div>
                    </div>
                  );
                })}
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