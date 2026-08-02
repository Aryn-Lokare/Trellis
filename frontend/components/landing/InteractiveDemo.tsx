'use client';

import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Volume2, 
  Table, 
  Network, 
  Search, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight,
  Sparkles,
  ExternalLink
} from 'lucide-react';

interface FileSource {
  id: string;
  name: string;
  type: 'pdf' | 'audio' | 'table' | 'diagram';
  color: string;
  details: string;
  icon: React.ComponentType<any>;
}

interface GraphNode {
  id: string;
  label: string;
  type: string;
  fileId: string;
  x: number;
  y: number;
}

interface GraphLink {
  source: string;
  target: string;
  label: string;
  type: 'verifies' | 'contradicts' | 'references';
}

interface SampleQuery {
  id: string;
  question: string;
  answer: string;
  citations: { text: string; fileId: string; highlightSpan: string }[];
  status: 'compliant' | 'warning';
}

export function InteractiveDemo() {
  const [activeQueryId, setActiveQueryId] = useState<string>('q1');
  const [hoveredFileId, setHoveredFileId] = useState<string | null>(null);
  const [hoveredCitationId, setHoveredCitationId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [typedQuestion, setTypedQuestion] = useState<string>('');

  const files: FileSource[] = [
    { id: 'f1', name: 'vendor-agreement-v4.pdf', type: 'pdf', color: '#ff7759', details: 'Clause 4.2: Restricted to EU servers', icon: FileText },
    { id: 'f2', name: 'internal-audit-q2.wav', type: 'audio', color: '#1863dc', details: 'Timestamp 04:12: Controller confirms EU storage', icon: Volume2 },
    { id: 'f3', name: 'transaction-log-june.csv', type: 'table', color: '#003c33', details: 'Row 89: DB backup transfer to US-East-1', icon: Table },
    { id: 'f4', name: 'network-topology.svg', type: 'diagram', color: '#9b60aa', details: 'Backup router routes to USA servers', icon: Network },
  ];

  const queries: Record<string, SampleQuery> = {
    q1: {
      id: 'q1',
      question: 'Are vendor data privacy terms compliant with EU data restrictions?',
      answer: 'Yes, according to the vendor agreement, data hosting is legally restricted to EU servers (vendor-agreement-v4.pdf [Page 12]). This was verbally confirmed by the controller during the audit call (internal-audit-q2.wav [04:12]). No external routes are documented in standard operational files.',
      citations: [
        { text: 'vendor-agreement-v4.pdf [Page 12]', fileId: 'f1', highlightSpan: 'Clause 4.2: Restricted to EU servers' },
        { text: 'internal-audit-q2.wav [04:12]', fileId: 'f2', highlightSpan: 'Timestamp 04:12: Controller confirms EU storage' }
      ],
      status: 'compliant'
    },
    q2: {
      id: 'q2',
      question: 'Check June backup transfers against security policies.',
      answer: 'Compliance Breach Detected: A transaction log entry records a database backup transferred to a US server (transaction-log-june.csv [Row 89]). This directly violates the legal restrictions in vendor-agreement-v4.pdf [Page 12] and bypasses the firewall diagrams shown in network-topology.svg [Router 3B].',
      citations: [
        { text: 'transaction-log-june.csv [Row 89]', fileId: 'f3', highlightSpan: 'Row 89: DB backup transfer to US-East-1' },
        { text: 'vendor-agreement-v4.pdf [Page 12]', fileId: 'f1', highlightSpan: 'Clause 4.2: Restricted to EU servers' },
        { text: 'network-topology.svg [Router 3B]', fileId: 'f4', highlightSpan: 'Backup router routes to USA servers' }
      ],
      status: 'warning'
    }
  };

  const currentQuery = queries[activeQueryId];

  // Graph data
  const nodes: GraphNode[] = [
    { id: 'n1', label: 'Clause 4.2 (GDPR)', type: 'clause', fileId: 'f1', x: 150, y: 80 },
    { id: 'n2', label: 'Audit Call Testimony', type: 'statement', fileId: 'f2', x: 80, y: 180 },
    { id: 'n3', label: 'Backup Transfer Event', type: 'event', fileId: 'f3', x: 280, y: 160 },
    { id: 'n4', label: 'Backup Route Config', type: 'system', fileId: 'f4', x: 220, y: 240 },
    { id: 'n5', label: 'EU Sovereignty Policy', type: 'regulation', fileId: 'f1', x: 180, y: 150 }
  ];

  const links: GraphLink[] = [
    { source: 'n2', target: 'n1', label: 'corroborates', type: 'verifies' },
    { source: 'n3', target: 'n1', label: 'violates', type: 'contradicts' },
    { source: 'n3', target: 'n4', label: 'executed-via', type: 'references' },
    { source: 'n1', target: 'n5', label: 'governs', type: 'references' },
    { source: 'n4', target: 'n5', label: 'bypasses', type: 'contradicts' }
  ];

  useEffect(() => {
    // Type-out effect when active query changes
    setIsTyping(true);
    setTypedQuestion('');
    let index = 0;
    const text = queries[activeQueryId].question;
    
    const interval = setInterval(() => {
      setTypedQuestion((prev) => prev + text.charAt(index));
      index++;
      if (index >= text.length) {
        clearInterval(interval);
        setIsTyping(false);
      }
    }, 15);

    return () => clearInterval(interval);
  }, [activeQueryId]);

  const activeFileIds = currentQuery.citations.map(c => c.fileId);

  return (
    <div className="grid gap-8 lg:grid-cols-12 items-stretch mt-12 max-w-7xl mx-auto">
      
      {/* LEFT COLUMN: SOURCE DOCUMENTS & KNOWLEDGE GRAPH */}
      <div className="lg:col-span-6 flex flex-col gap-6">
        
        {/* Document Sources Panel */}
        <div className="bg-white rounded-[22px] border border-[#d9d9dd] p-6 flex flex-col gap-4 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-[#edfce9]/40 rounded-full blur-2xl pointer-events-none" />
          
          <div className="flex items-center justify-between border-b border-[#d9d9dd] pb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#ff7759] animate-pulse" />
              <span className="mono-label text-xs font-semibold text-[#212121]">INCOMING MULTI-FORMAT EVIDENCE</span>
            </div>
            <span className="mono-label text-[10px] text-[#93939f]">4 FILES LOADED</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {files.map((file) => {
              const FileIcon = file.icon;
              const isCited = activeFileIds.includes(file.id);
              const isHovered = hoveredFileId === file.id || hoveredCitationId === file.id;

              return (
                <div
                  key={file.id}
                  className={`p-4 rounded-xl border transition-all duration-300 flex flex-col justify-between ${
                    isHovered 
                      ? 'border-[#ff7759] bg-[#ff7759]/5 shadow-[0_4px_12px_rgba(255,119,89,0.08)] scale-[1.02]' 
                      : isCited 
                        ? 'border-[#17171c] bg-[#eeece7]/40' 
                        : 'border-[#d9d9dd] bg-white opacity-60'
                  }`}
                  onMouseEnter={() => setHoveredFileId(file.id)}
                  onMouseLeave={() => setHoveredFileId(null)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="p-2 rounded-lg text-white"
                        style={{ backgroundColor: file.color }}
                      >
                        <FileIcon className="w-4 h-4" />
                      </div>
                      <div className="flex flex-col min-w-0">
                        <span className="text-xs font-medium text-[#212121] truncate font-mono">
                          {file.name}
                        </span>
                        <span className="text-[10px] mono-label text-[#93939f] mt-0.5">
                          {file.type.toUpperCase()} SOURCE
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-[#d9d9dd]/60 flex flex-col gap-1">
                    <span className="text-[10px] text-[#93939f] font-mono">EXTRACTED SPAN:</span>
                    <span className="text-[11px] text-[#212121] font-mono font-medium leading-normal italic truncate">
                      "{file.details}"
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Knowledge Graph Rendering Block */}
        <div className="bg-[#eeece7] rounded-[22px] border border-[#d9d9dd] p-6 flex flex-col gap-4 shadow-sm relative overflow-hidden flex-1 min-h-[300px]">
          <div className="flex items-center justify-between border-b border-[#d9d9dd] pb-3">
            <div className="flex items-center gap-2">
              <Network className="w-4 h-4 text-[#ff7759]" />
              <span className="mono-label text-xs font-semibold text-[#212121]">CONNECTED KNOWLEDGE GRAPH</span>
            </div>
            <span className="mono-label text-[10px] text-[#93939f]">5 ENTITIES • 5 LINKS</span>
          </div>

          <div className="relative w-full h-[240px] mt-2 bg-white rounded-xl border border-[#d9d9dd]/80 overflow-hidden">
            {/* SVG Graph connections */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              <defs>
                <marker id="arrow-verifies" viewBox="0 0 10 10" refX="15" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
                </marker>
                <marker id="arrow-contradicts" viewBox="0 0 10 10" refX="15" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 10 5 L 0 9 z" fill="#ff7759" />
                </marker>
                <marker id="arrow-references" viewBox="0 0 10 10" refX="15" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 10 5 L 0 9 z" fill="#75758a" />
                </marker>
                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Links */}
              {links.map((link, idx) => {
                const sNode = nodes.find(n => n.id === link.source);
                const tNode = nodes.find(n => n.id === link.target);
                if (!sNode || !tNode) return null;

                const isLinkActive = 
                  (activeFileIds.includes(sNode.fileId) && activeFileIds.includes(tNode.fileId)) ||
                  hoveredFileId === sNode.fileId || hoveredFileId === tNode.fileId;

                let strokeColor = '#d9d9dd';
                if (isLinkActive) {
                  if (link.type === 'verifies') strokeColor = '#10b981';
                  else if (link.type === 'contradicts') strokeColor = '#ff7759';
                  else strokeColor = '#75758a';
                }

                return (
                  <g key={idx} className="transition-all duration-300">
                    <line
                      x1={sNode.x}
                      y1={sNode.y}
                      x2={tNode.x}
                      y2={tNode.y}
                      stroke={strokeColor}
                      strokeWidth={isLinkActive ? 2 : 1}
                      strokeDasharray={link.type === 'contradicts' && isLinkActive ? '4,4' : '0'}
                      markerEnd={`url(#arrow-${link.type})`}
                    />
                    {isLinkActive && (
                      <text
                        x={(sNode.x + tNode.x) / 2}
                        y={(sNode.y + tNode.y) / 2 - 5}
                        fill={strokeColor}
                        fontSize="9"
                        className="font-mono text-center font-bold bg-white"
                        textAnchor="middle"
                      >
                        {link.label.toUpperCase()}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>

            {/* Nodes */}
            {nodes.map((node) => {
              const isCited = activeFileIds.includes(node.fileId);
              const isHovered = hoveredFileId === node.fileId || hoveredCitationId === node.fileId;
              const file = files.find(f => f.id === node.fileId);

              return (
                <div
                  key={node.id}
                  className="absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-all duration-300 group z-10"
                  style={{ left: node.x, top: node.y }}
                  onMouseEnter={() => setHoveredFileId(node.fileId)}
                  onMouseLeave={() => setHoveredFileId(null)}
                >
                  <div 
                    className={`px-2.5 py-1.5 rounded-full border text-[10px] font-mono font-medium shadow-sm transition-all flex items-center gap-1.5 ${
                      isHovered
                        ? 'border-[#ff7759] bg-[#ff7759] text-white scale-110 shadow-md ring-4 ring-[#ff7759]/20'
                        : isCited
                          ? 'border-[#17171c] bg-[#17171c] text-white'
                          : 'border-[#d9d9dd] bg-white text-[#616161]'
                    }`}
                  >
                    <span 
                      className="w-1.5 h-1.5 rounded-full"
                      style={{ 
                        backgroundColor: isHovered || isCited ? '#ffffff' : (file?.color || '#93939f') 
                      }}
                    />
                    {node.label}
                  </div>
                  {/* Tooltip */}
                  <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 hidden group-hover:block bg-[#17171c] text-white text-[9px] font-mono px-2 py-1 rounded whitespace-nowrap shadow z-20">
                    Source: {file?.name}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* RIGHT COLUMN: INTERACTIVE AGENT CHAT CONSOLE */}
      <div className="lg:col-span-6 flex flex-col justify-between bg-[#17171c] text-white rounded-[22px] p-6 shadow-xl border border-white/5 relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute -top-20 -right-20 w-44 h-44 bg-[#003c33]/40 rounded-full blur-3xl pointer-events-none" />
        
        <div>
          {/* Header */}
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#ff7759]" />
              <span className="mono-label text-xs tracking-wider text-white">TRELLIS EVIDENCE COMPILER</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="mono-label text-[9px] text-[#93939f]">GROUNDED MODE ACTIVE</span>
            </div>
          </div>

          {/* Sample Query Selectors */}
          <div className="mt-5">
            <span className="text-[10px] mono-label text-[#93939f] block mb-2">SELECT INVESTIGATION PROMPT</span>
            <div className="flex flex-col gap-2">
              <button
                onClick={() => setActiveQueryId('q1')}
                className={`text-left p-3.5 rounded-xl border text-xs transition-all flex items-center justify-between ${
                  activeQueryId === 'q1'
                    ? 'border-[#ff7759] bg-white/5 text-white'
                    : 'border-white/10 bg-transparent text-[#93939f] hover:text-white hover:bg-white/5'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <span className="font-mono text-[#ff7759]">01 /</span>
                  <span className="truncate">{queries.q1.question}</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 shrink-0" />
              </button>
              
              <button
                onClick={() => setActiveQueryId('q2')}
                className={`text-left p-3.5 rounded-xl border text-xs transition-all flex items-center justify-between ${
                  activeQueryId === 'q2'
                    ? 'border-[#ff7759] bg-white/5 text-white'
                    : 'border-white/10 bg-transparent text-[#93939f] hover:text-white hover:bg-white/5'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <span className="font-mono text-[#ff7759]">02 /</span>
                  <span className="truncate">{queries.q2.question}</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 shrink-0" />
              </button>
            </div>
          </div>

          {/* Terminal Search bar */}
          <div className="mt-6 bg-black/40 border border-white/10 rounded-xl p-3.5 flex items-center gap-3">
            <Search className="w-4 h-4 text-[#93939f]" />
            <div className="flex-1 font-mono text-xs text-white">
              {typedQuestion}
              {isTyping && <span className="animate-pulse">|</span>}
            </div>
          </div>

          {/* Animated Output Window */}
          <div className="mt-6 min-h-[220px]">
            {isTyping ? (
              <div className="flex flex-col items-center justify-center py-12 gap-3">
                <div className="w-6 h-6 border-2 border-[#ff7759] border-t-transparent rounded-full animate-spin" />
                <span className="text-[10px] mono-label text-[#93939f] tracking-widest animate-pulse animate-duration-1000">
                  WALKING RELATIONSHIP GRAPH & COMPILING CITATIONS
                </span>
              </div>
            ) : (
              <div className="animate-fadeIn flex flex-col gap-4">
                
                {/* Result header / status */}
                <div className="flex items-center gap-2">
                  {currentQuery.status === 'compliant' ? (
                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span className="mono-label text-[9px] font-bold">VERIFIED VERDICT: COMPLIANT</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#ff7759]/10 border border-[#ff7759]/30 text-[#ff7759]">
                      <AlertCircle className="w-3.5 h-3.5" />
                      <span className="mono-label text-[9px] font-bold">VERIFIED VERDICT: DEVIATION DETECTED</span>
                    </div>
                  )}
                </div>

                {/* Generated Answer text */}
                <div className="text-sm leading-relaxed text-white/90 font-sans">
                  {/* We parse the answer text and highlight citations */}
                  {currentQuery.answer.split(/(\[.*?\])/).map((part, index) => {
                    const isCitation = part.startsWith('[') && part.endsWith(']');
                    if (isCitation) {
                      const citationText = part.slice(1, -1);
                      const citationObj = currentQuery.citations.find(c => citationText.includes(c.fileId) || c.text.includes(citationText));
                      const fileId = citationObj?.fileId || 'f1';
                      const file = files.find(f => f.id === fileId);

                      return (
                        <span
                          key={index}
                          className="mx-0.5 inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono cursor-pointer transition-all border font-bold"
                          style={{
                            borderColor: file?.color + '50',
                            backgroundColor: file?.color + '15',
                            color: file?.color || '#ff7759'
                          }}
                          onMouseEnter={() => setHoveredCitationId(fileId)}
                          onMouseLeave={() => setHoveredCitationId(null)}
                        >
                          {citationText}
                        </span>
                      );
                    }
                    return part;
                  })}
                </div>

                {/* Citations breakdown */}
                <div className="mt-4 pt-4 border-t border-white/5">
                  <span className="text-[10px] mono-label text-[#93939f] block mb-2">VERIFIED CITED EVIDENCE PATHS</span>
                  <div className="flex flex-col gap-2">
                    {currentQuery.citations.map((cit, idx) => {
                      const file = files.find(f => f.id === cit.fileId);
                      return (
                        <div 
                          key={idx}
                          className="flex items-center justify-between text-xs p-2 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <span 
                              className="w-1.5 h-1.5 rounded-full" 
                              style={{ backgroundColor: file?.color }}
                            />
                            <span className="font-mono text-white/80">{cit.text}</span>
                          </div>
                          <span className="font-mono text-[10px] text-[#93939f] italic">
                            {cit.highlightSpan}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-[11px] text-[#93939f]">
          <span>Grounded in Connected Graph Database</span>
          <a 
            href="/upload"
            className="flex items-center gap-1 text-[#ff7759] hover:underline font-mono text-[10px]"
          >
            <span>Open Sandbox Workspace</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

    </div>
  );
}
