'use client';

import React from 'react';
import { FileText, Music, Table as TableIcon, Image as ImageIcon, Database } from 'lucide-react';
import { useDocumentList } from '../../hooks/useDocument';
import { Badge } from '../ui/badge';
import { Skeleton } from '../ui/skeleton';
import { formatDate } from '../../lib/utils';
import { Document, DocumentType } from '../../types';
import { InlineState } from '../ui/InlineState';

export function DocumentListTable() {
  const { data: documents, isLoading, isError, error, refetch } = useDocumentList();

  const getDocIcon = (type: DocumentType) => {
    switch (type) {
      case 'audio':
        return Music;
      case 'table':
        return TableIcon;
      case 'schematic':
        return ImageIcon;
      case 'pdf':
      default:
        return FileText;
    }
  };

  return (
    <div className="bg-[#eeece7] border border-[#d9d9dd] rounded-[8px] p-6 sm:p-8">
      <div className="flex items-center justify-between pb-4 border-b border-[#d9d9dd] mb-4">
        <div>
          <span className="mono-label text-[#1863dc]">DOCUMENT REPOSITORY</span>
          <h3 className="text-xl font-medium tracking-tight text-[#212121] mt-0.5">
            Ingested Evidence Library
          </h3>
        </div>
        {documents && (
          <span className="mono-label text-xs bg-[#eeece7] text-[#212121] px-3 py-1 rounded-full">
            {documents.length} DOCUMENTS INGESTED
          </span>
        )}
      </div>

      {isLoading && (
        <div className="space-y-3 py-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      )}

      {isError && (
        <InlineState
          label="Failed to fetch documents"
          cause={error?.message || 'Could not connect to the backend document repository.'}
          onRetry={() => refetch()}
        />
      )}

      {!isLoading && !isError && documents && documents.length === 0 && (
        <div className="py-12 text-center border border-dashed border-[#d9d9dd] rounded-[8px] bg-white/50 p-8">
          <Database className="w-10 h-10 text-[#93939f] mx-auto mb-3" />
          <span className="mono-label text-[#616161] block">KNOWLEDGE GRAPH IS EMPTY</span>
          <p className="text-sm text-[#93939f] mt-1 max-w-sm mx-auto">
            No compliance documents have been ingested yet. Upload PDF, audio recordings, or tables above to build the graph.
          </p>
        </div>
      )}

      {!isLoading && !isError && documents && documents.length > 0 && (
        <div className="divide-y divide-[#d9d9dd] overflow-x-auto">
          <div className="grid grid-cols-12 gap-4 pb-2 px-2 mono-label text-[11px] text-[#93939f] font-semibold">
            <div className="col-span-5 sm:col-span-6">FILENAME & ID</div>
            <div className="col-span-3 sm:col-span-3">TYPE & STATUS</div>
            <div className="col-span-4 sm:col-span-3 text-right">DATE INGESTED</div>
          </div>

          {documents.map((doc: Document) => {
            const Icon = getDocIcon(doc.type);
            return (
              <div
                key={doc.id}
                className="grid grid-cols-12 gap-4 py-3.5 px-2 items-center hover:bg-[#eeece7]/40 rounded-[8px] transition-colors"
              >
                <div className="col-span-5 sm:col-span-6 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-[6px] bg-[#eeece7] text-[#17171c] flex items-center justify-center shrink-0">
                    <Icon className="w-4 h-4 text-[#17171c]" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[#212121] truncate">{doc.filename}</p>
                    <p className="mono-label text-[10px] text-[#93939f] truncate">ID: {doc.id}</p>
                  </div>
                </div>

                <div className="col-span-3 sm:col-span-3 flex items-center gap-2">
                  <Badge variant="outline" entityType={doc.type}>
                    {doc.type}
                  </Badge>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 hidden sm:inline-block" />
                </div>

                <div className="col-span-4 sm:col-span-3 text-right text-xs text-[#75758a] font-mono">
                  {formatDate(doc.created_at)}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
