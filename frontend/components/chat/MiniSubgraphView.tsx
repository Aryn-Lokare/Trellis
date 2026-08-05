'use client';

import React from 'react';
import Link from 'next/link';
import { Subgraph, Entity, Relationship } from '../../types';
import { Badge } from '../ui/badge';
import { GitFork, ArrowUpRight, Link2 } from 'lucide-react';
import { useComplianceStore } from '../../store/useComplianceStore';
import { cn } from '../../lib/utils';
import { SubgraphCanvas } from '../graph/SubgraphCanvas';

interface MiniSubgraphViewProps {
  subgraph: Subgraph;
}

export function MiniSubgraphView({ subgraph }: MiniSubgraphViewProps) {
  const setActiveSubgraph = useComplianceStore((state) => state.setActiveSubgraph);

  if (!subgraph || (!subgraph.nodes?.length && !subgraph.edges?.length)) {
    return null;
  }

  const handleDeepLink = () => {
    setActiveSubgraph(subgraph);
  };

  // Helper to determine entity styling by type
  const getEntityStyles = (type: string) => {
    const t = type.toLowerCase();
    if (t.includes('clause') || t.includes('regulation') || t.includes('policy') || t.includes('law')) {
      return 'text-[#ff7759] border-[#ff7759]/20 bg-[#ff7759]/10'; // Coral
    }
    if (t.includes('actor') || t.includes('person') || t.includes('company') || t.includes('vendor')) {
      return 'text-[#1863dc] border-[#1863dc]/20 bg-[#1863dc]/10'; // Action Blue
    }
    if (t.includes('system') || t.includes('database') || t.includes('router') || t.includes('network') || t.includes('server')) {
      return 'text-[#9b60aa] border-[#9b60aa]/20 bg-[#9b60aa]/10'; // Purple
    }
    if (t.includes('date') || t.includes('time') || t.includes('deadline')) {
      return 'text-[#10b981] border-[#10b981]/20 bg-[#10b981]/10'; // Emerald Green
    }
    return 'text-[#93939f] border-white/10 bg-white/5'; // Muted Default
  };

  return (
    <div className="bg-gradient-to-br from-[#041210] to-[#0a201c] text-white rounded-[22px] p-6 border border-[#0d3630] space-y-6 relative overflow-hidden shadow-lg">
      {/* Mesh green glow overlay */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-[#10b981]/10 rounded-full blur-3xl pointer-events-none" />
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-4">
        <div className="flex items-center gap-2.5">
          <GitFork className="w-5 h-5 text-[#ff7759]" />
          <span className="font-semibold tracking-tight text-sm font-display text-white">
            REASONING SUBGRAPH EXTRACTED
          </span>
        </div>
      </div>

      {/* Embedded Dynamic Interactive Force Graph */}
      <div className="w-full overflow-hidden rounded-[16px] border border-white/10 shadow-inner">
        <SubgraphCanvas graphData={subgraph} height="h-[380px]" />
      </div>

      {/* Nodes / Entities Strip */}
      <div className="space-y-3">
        <span className="mono-label text-[10px] text-white/50 block font-bold tracking-wider">
          TRAVERSED KNOWLEDGE ENTITIES ({subgraph.nodes?.length || 0})
        </span>
        <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
          {subgraph.nodes?.map((node: Entity) => (
            <div
              key={node.id}
              className={cn(
                "border px-3 py-1.5 rounded-[8px] text-xs flex items-center gap-2 transition-all hover:scale-[1.02] cursor-default",
                getEntityStyles(node.type)
              )}
            >
              <span className="font-medium text-white">{node.name}</span>
              <span className="text-[8px] font-mono font-bold uppercase px-1 py-0.2 rounded-sm bg-black/35 border border-white/5">
                {node.type}
              </span>
              {node.source_span && (
                <span className="mono-label text-[9px] text-[#ffad9b]/80 font-mono">
                  [{node.source_span}]
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Relationships / Edges List */}
      {subgraph.edges && subgraph.edges.length > 0 && (
        <div className="space-y-3 pt-4 border-t border-white/5">
          <span className="mono-label text-[10px] text-white/50 block font-bold tracking-wider">
            DETECTED RELATIONSHIP PATHS ({subgraph.edges.length})
          </span>
          <div className="space-y-2 max-h-48 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
            {subgraph.edges.map((edge: Relationship) => {
              const srcNode = subgraph.nodes?.find((n) => n.id === edge.source_entity_id)?.name || edge.source_entity_id;
              const tgtNode = subgraph.nodes?.find((n) => n.id === edge.target_entity_id)?.name || edge.target_entity_id;

              return (
                <div
                  key={edge.id}
                  className="flex items-center gap-3 bg-black/20 hover:bg-black/30 border border-white/5 hover:border-white/10 px-4 py-2.5 rounded-xl text-xs font-mono transition-all"
                >
                  <span className="text-white font-medium truncate max-w-[200px] shrink-0">{srcNode}</span>
                  <div className="flex-1 flex items-center justify-center min-w-[120px] relative px-2">
                    <div className="absolute inset-x-0 h-[1px] bg-white/10" />
                    <span className="relative z-10 px-2.5 py-0.5 rounded-full bg-[#17171c] text-[#ff7759] text-[9px] font-bold border border-white/10 uppercase tracking-wider">
                      {edge.relationship_type}
                    </span>
                  </div>
                  <span className="text-white font-medium truncate max-w-[200px] shrink-0">{tgtNode}</span>
                  {edge.source_span && (
                    <span className="text-[10px] text-[#ffad9b] shrink-0 font-mono ml-2 opacity-80 bg-white/5 border border-white/5 px-1.5 py-0.5 rounded">
                      [{edge.source_span}]
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
