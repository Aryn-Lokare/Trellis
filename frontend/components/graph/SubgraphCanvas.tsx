'use client';

import React, { useRef, useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Entity, Relationship, Subgraph } from '../../types';
import { getEntityTypeColor } from '../../lib/theme';
import { useComplianceStore } from '../../store/useComplianceStore';
import { GitFork, Layers, RotateCcw } from 'lucide-react';

const ForceGraph2D = dynamic<any>(
  () => import('react-force-graph-2d').then((mod) => mod.default || mod),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex items-center justify-center text-[#ffad9b] font-mono text-xs">
        Initializing 2D Knowledge Graph Physics Engine...
      </div>
    ),
  }
);

interface SubgraphCanvasProps {
  graphData: Subgraph;
  filterType?: string | null;
}

export function SubgraphCanvas({ graphData, filterType }: SubgraphCanvasProps) {
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const setSelectedNode = useComplianceStore((state) => state.setSelectedNode);
  const setSelectedEdge = useComplianceStore((state) => state.setSelectedEdge);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth || 800,
          height: containerRef.current.clientHeight || 600,
        });
      }
    };
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const formattedNodes = (graphData.nodes || [])
    .filter((n) => !filterType || filterType === 'ALL' || n.type.toLowerCase() === filterType.toLowerCase())
    .map((n) => ({
      id: n.id,
      name: n.name,
      type: n.type,
      color: getEntityTypeColor(n.type),
      val: n.type === 'regulation' || n.type === 'vendor' ? 8 : 5,
      raw: n,
    }));

  const formattedNodeIds = new Set(formattedNodes.map((n) => n.id));

  const formattedLinks = (graphData.edges || [])
    .filter((e) => formattedNodeIds.has(e.source_entity_id) && formattedNodeIds.has(e.target_entity_id))
    .map((e) => ({
      id: e.id,
      source: e.source_entity_id,
      target: e.target_entity_id,
      label: e.relationship_type,
      raw: e,
    }));

  const handleNodeClick = (node: any) => {
    if (node && node.raw) {
      setSelectedNode(node.raw);
    }
  };

  const handleLinkClick = (link: any) => {
    if (link && link.raw) {
      setSelectedEdge(link.raw);
    }
  };

  const handleZoomReset = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 50);
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative w-full h-[650px] bg-[#071829] rounded-[22px] border border-[#003c33] overflow-hidden shadow-2xl"
    >
      <div className="absolute top-4 left-4 z-10 bg-[#17171c]/90 backdrop-blur border border-white/10 px-4 py-2 rounded-full flex items-center gap-3 text-white">
        <GitFork className="w-4 h-4 text-[#ff7759]" />
        <span className="mono-label text-xs">
          SUBGRAPH CANVAS • {formattedNodes.length} NODES / {formattedLinks.length} EDGES
        </span>
      </div>

      <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
        <button
          onClick={handleZoomReset}
          className="bg-[#17171c]/90 hover:bg-black text-[#ff7759] p-2.5 rounded-full border border-white/10 transition-all cursor-pointer"
          title="Reset Zoom & Center Graph"
        >
          <RotateCcw className="w-4 h-4 text-[#ff7759]" />
        </button>
      </div>

      {dimensions.width > 0 && (
        <ForceGraph2D
          ref={fgRef}
          width={dimensions.width}
          height={dimensions.height}
          graphData={{ nodes: formattedNodes, links: formattedLinks }}
          nodeLabel={(node: any) => `${node.name} (${node.type.toUpperCase()})`}
          nodeColor={(node: any) => node.color}
          nodeRelSize={6}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkLabel={(link: any) => link.label}
          linkColor={() => 'rgba(217, 217, 221, 0.4)'}
          linkWidth={1.5}
          onNodeClick={handleNodeClick}
          onLinkClick={handleLinkClick}
          nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
            const label = node.name;
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px monospace`;

            ctx.beginPath();
            ctx.arc(node.x, node.y, node.val || 6, 0, 2 * Math.PI, false);
            ctx.fillStyle = node.color || '#ff7759';
            ctx.fill();
            ctx.lineWidth = 1.5 / globalScale;
            ctx.strokeStyle = '#ffffff';
            ctx.stroke();

            if (globalScale > 0.6) {
              ctx.fillStyle = '#ffffff';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'top';
              ctx.fillText(label, node.x, node.y + (node.val || 6) + 2);
            }
          }}
        />
      )}
    </div>
  );
}
