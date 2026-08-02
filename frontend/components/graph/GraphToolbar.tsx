'use client';

import React from 'react';
import { RefreshCw, Filter, Layers } from 'lucide-react';
import { Button } from '../ui/button';

interface GraphToolbarProps {
  onRefresh: () => void;
  isRefetching: boolean;
  activeFilter: string;
  onFilterChange: (filter: string) => void;
  nodeTypes: string[];
}

export function GraphToolbar({
  onRefresh,
  isRefetching,
  activeFilter,
  onFilterChange,
  nodeTypes,
}: GraphToolbarProps) {
  const filterOptions = ['ALL', ...Array.from(new Set(nodeTypes))];

  return (
    <div className="bg-[#eeece7] border border-[#d9d9dd] rounded-[8px] p-4 flex flex-wrap items-center justify-between gap-4">
      {/* Entity Filter Pill Strip */}
      <div className="flex items-center gap-2 overflow-x-auto py-1">
        <span className="mono-label text-xs text-[#93939f] flex items-center gap-1.5 shrink-0 mr-2">
          <Filter className="w-3.5 h-3.5 text-[#ff7759]" />
          <span>TAXONOMY FILTER:</span>
        </span>

        {filterOptions.map((type) => {
          const isSelected = activeFilter === type;
          return (
            <button
              key={type}
              onClick={() => onFilterChange(type)}
              className={`mono-label text-[11px] px-3 py-1.5 rounded-full border transition-all shrink-0 cursor-pointer ${
                isSelected
                  ? 'bg-[#17171c] text-white border-[#17171c] font-bold'
                  : 'bg-transparent text-[#616161] border-[#d9d9dd] hover:bg-[#eeece7]'
              }`}
            >
              {type}
            </button>
          );
        })}
      </div>

      {/* Real-time Refresh Action */}
      <Button
        onClick={onRefresh}
        disabled={isRefetching}
        variant="outline"
        size="sm"
        className="shrink-0"
      >
        <RefreshCw className={`w-3.5 h-3.5 ${isRefetching ? 'animate-spin text-[#ff7759]' : ''}`} />
        <span>{isRefetching ? 'Updating Subgraph...' : 'Sync Ingested Graph'}</span>
      </Button>
    </div>
  );
}
