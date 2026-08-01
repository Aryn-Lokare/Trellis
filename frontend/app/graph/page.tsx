'use client';

import React, { useState } from 'react';
import { SubgraphCanvas } from '../../components/graph/SubgraphCanvas';
import { GraphToolbar } from '../../components/graph/GraphToolbar';
import { GraphNodeDetail } from '../../components/graph/GraphNodeDetail';
import { useGraph } from '../../hooks/useGraph';
import { useComplianceStore } from '../../store/useComplianceStore';
import { Skeleton } from '../../components/ui/skeleton';
import { Database } from 'lucide-react';
import Link from 'next/link';
import { InlineState } from '../../components/ui/InlineState';

export default function GraphPage() {
  const { data: fetchGraph, isLoading, isError, error, refetch, isRefetching } = useGraph();
  const activeSubgraph = useComplianceStore((state) => state.activeSubgraph);
  const [filterType, setFilterType] = useState<string>('ALL');

  const currentGraphData = activeSubgraph || fetchGraph || { nodes: [], edges: [] };

  const nodeTypes = Array.from(
    new Set((currentGraphData.nodes || []).map((n) => n.type))
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="border-b border-[#d9d9dd] pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <span className="mono-label text-[#003c33]">STEP 3 OF 3 • VISUAL KNOWLEDGE GRAPH</span>
          <h1 className="text-4xl sm:text-5xl font-medium tracking-tight text-[#17171c] mt-1">
            Knowledge Subgraph Topology
          </h1>
          <p className="text-base text-[#616161] max-w-2xl mt-2">
            Explore the extracted entity nodes (regulations, vendors, policies, systems) and relationship edges connecting your compliance evidence across all formats.
          </p>
        </div>

        {activeSubgraph && (
          <button
            onClick={() => useComplianceStore.getState().setActiveSubgraph(null)}
            className="mono-label text-xs bg-[#ff7759]/10 text-[#ff7759] border border-[#ff7759]/30 px-3 py-1.5 rounded-full cursor-pointer"
          >
            SHOW FULL GRAPH (EXIT QUERY SUBGRAPH)
          </button>
        )}
      </div>

      {/* Toolbar Controls */}
      <GraphToolbar
        onRefresh={() => refetch()}
        isRefetching={isRefetching}
        activeFilter={filterType}
        onFilterChange={setFilterType}
        nodeTypes={nodeTypes}
      />

      {/* The graph remains a product surface even when the live endpoint has no result. */}
      <section className="dark-feature-band min-h-[650px] p-4 sm:p-6">
        {isLoading ? (
          <Skeleton className="w-full h-[600px] rounded-[16px] bg-white/10" />
        ) : isError ? (
          <div className="mx-auto flex h-[600px] max-w-xl items-center">
            <InlineState
              label="Failed to fetch knowledge graph"
              cause={error?.message || 'Could not connect to backend /graph endpoint.'}
              onRetry={() => refetch()}
              tone="dark"
              className="w-full"
            />
          </div>
        ) : currentGraphData.nodes.length === 0 ? (
          <div className="flex h-[600px] flex-col items-center justify-center text-center">
            <Database className="w-10 h-10 text-[#ff7759] mb-4" />
            <span className="mono-label text-[#ffad9b] block text-sm">KNOWLEDGE GRAPH HAS NO ENTITIES YET</span>
            <p className="text-sm text-white/65 mt-1 max-w-md">
              Ingest PDFs, audio recordings, or tables on the Upload page to populate the Knowledge Graph.
            </p>
            <Link href="/upload" className="button-secondary !text-white mt-4 text-xs">
              Go to Upload & Ingestion
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-8 xl:col-span-9">
              <SubgraphCanvas graphData={currentGraphData} filterType={filterType} />
            </div>
            <div className="lg:col-span-4 xl:col-span-3">
              <GraphNodeDetail />
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
