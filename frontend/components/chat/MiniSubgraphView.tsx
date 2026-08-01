'use client';

import React from 'react';
import Link from 'next/link';
import { Subgraph, Entity, Relationship } from '../../types';
import { Badge } from '../ui/badge';
import { GitFork, ExternalLink, ShieldCheck, ArrowRight } from 'lucide-react';
import { useComplianceStore } from '../../store/useComplianceStore';

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

  return (
    <div className="bg-[#003c33] text-white rounded-[16px] p-5 border border-[#003c33] space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitFork className="w-5 h-5 text-[#ff7759]" />
          <span className="mono-label text-white">REASONING SUBGRAPH EXTRACTED</span>
        </div>
        <Link
          href="/graph"
          onClick={handleDeepLink}
          className="inline-flex items-center gap-1.5 text-xs font-mono text-[#ffad9b] hover:text-white underline transition-colors"
        >
          <span>Full Interactive Graph</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Nodes / Entities Strip */}
      <div className="space-y-2">
        <span className="mono-label text-[10px] text-[#edfce9]/70">
          TRAVERSED KNOWLEDGE ENTITIES ({subgraph.nodes?.length || 0}):
        </span>
        <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
          {subgraph.nodes?.map((node: Entity) => (
            <div
              key={node.id}
              className="bg-white/10 hover:bg-white/20 border border-white/20 px-3 py-1.5 rounded-[6px] text-xs flex items-center gap-2 transition-colors"
            >
              <span className="font-medium text-white">{node.name}</span>
              <Badge variant="outline" entityType={node.type} className="text-[9px] py-0">
                {node.type}
              </Badge>
              {node.source_span && (
                <span className="mono-label text-[9px] text-[#ffad9b] font-mono">
                  [{node.source_span}]
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Relationships / Edges List */}
      {subgraph.edges && subgraph.edges.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-white/10">
          <span className="mono-label text-[10px] text-[#edfce9]/70">
            DETECTED RELATIONSHIP PATHS ({subgraph.edges.length}):
          </span>
          <div className="space-y-1.5">
            {subgraph.edges.slice(0, 4).map((edge: Relationship) => {
              const srcNode = subgraph.nodes?.find((n) => n.id === edge.source_entity_id)?.name || edge.source_entity_id;
              const tgtNode = subgraph.nodes?.find((n) => n.id === edge.target_entity_id)?.name || edge.target_entity_id;

              return (
                <div
                  key={edge.id}
                  className="text-xs bg-black/20 px-3 py-1.5 rounded-[6px] flex items-center justify-between font-mono"
                >
                  <div className="flex items-center gap-2 truncate">
                    <span className="text-white font-medium truncate">{srcNode}</span>
                    <span className="text-[#ff7759] text-[10px] px-1.5 py-0.5 bg-black/40 rounded uppercase">
                      -- {edge.relationship_type} --&gt;
                    </span>
                    <span className="text-white font-medium truncate">{tgtNode}</span>
                  </div>
                  {edge.source_span && (
                    <span className="text-[10px] text-[#ffad9b] shrink-0 ml-2">
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
