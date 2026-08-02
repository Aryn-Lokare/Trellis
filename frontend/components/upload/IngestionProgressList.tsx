'use client';

import React from 'react';
import { Loader2, CheckCircle2, XCircle, Activity } from 'lucide-react';
import { useIngestionStatus } from '../../hooks/useIngestionStatus';
import { Badge } from '../ui/badge';
import { IngestionStepStatus } from '../../types';
import { InlineState } from '../ui/InlineState';

// --------------------------------------------------------------------------
//  Per-document progress card (renders one row in the list)
// --------------------------------------------------------------------------

function IngestionProgressItem({ documentId }: { documentId: string }) {
  const { data: status, isLoading, isError, error, refetch } = useIngestionStatus(documentId);

  const steps: { key: IngestionStepStatus; label: string }[] = [
    { key: 'queued', label: '1. Queued' },
    { key: 'parsing', label: '2. Parsing' },
    { key: 'extracting', label: '3. Extracting' },
    { key: 'completed', label: '4. Complete' },
  ];

  const getStepState = (stepKey: IngestionStepStatus, currentStatus?: IngestionStepStatus) => {
    if (!currentStatus) return 'pending';
    const statusOrder: IngestionStepStatus[] = ['queued', 'parsing', 'extracting', 'completed'];
    const currentIndex = statusOrder.indexOf(currentStatus);
    const stepIndex = statusOrder.indexOf(stepKey);

    if (currentStatus === 'failed') {
      return stepIndex <= currentIndex ? 'failed' : 'pending';
    }

    if (stepIndex < currentIndex || currentStatus === 'completed') return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="bg-[#1c1c24] rounded-[14px] p-4 border border-[#2a2a35]">
      {/* Header row */}
      <div className="flex items-center justify-between pb-3 border-b border-[#2a2a35] mb-3">
        <span className="mono-label text-xs text-[#93939f]">
          DOC&nbsp;{documentId.slice(0, 8)}
        </span>
        {status && (
          <Badge variant={status.status === 'completed' ? 'solid' : status.status === 'failed' ? 'solid' : 'coral'}>
            {status.status.toUpperCase()}
          </Badge>
        )}
      </div>

      {isLoading && (
        <div className="flex items-center py-4 text-[#93939f] gap-3">
          <Loader2 className="w-4 h-4 animate-spin text-[#1863dc]" />
          <span className="mono-label text-[10px]">POLLING...</span>
        </div>
      )}

      {isError && (
        <InlineState
          label="Failed to fetch status"
          cause={error?.message || 'Unknown error'}
          onRetry={() => refetch()}
          tone="dark"
        />
      )}

      {status && (
        <div className="space-y-3">
          {/* Filename */}
          <span className="text-sm font-medium text-[#eeece7] block truncate">
            {status.filename || 'Document'}
          </span>

          {/* Progress Bar */}
          <div className="w-full bg-[#2a2a35] h-1.5 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                status.status === 'failed'
                  ? 'bg-[#b30000]'
                  : status.status === 'completed'
                  ? 'bg-emerald-500'
                  : 'bg-[#ff7759]'
              }`}
              style={{ width: `${status.progress_percent || (status.status === 'completed' ? 100 : 45)}%` }}
            />
          </div>

          {/* Step Progression */}
          <div className="grid grid-cols-4 gap-1.5">
            {steps.map((step) => {
              const state = getStepState(step.key, status.status);
              return (
                <div
                  key={step.key}
                  className={`p-2 rounded-[6px] border text-[10px] flex items-center gap-1.5 ${
                    state === 'completed'
                      ? 'border-emerald-900/50 bg-emerald-950/20 text-emerald-400'
                      : state === 'active'
                      ? 'border-[#ff7759] bg-[#ff7759]/10 text-white'
                      : state === 'failed'
                      ? 'border-[#b30000] bg-[#b30000]/20 text-[#b30000]'
                      : 'border-[#2a2a35] bg-[#1c1c24] text-[#75758a]'
                  }`}
                >
                  {state === 'completed' && <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />}
                  {state === 'active' && <Loader2 className="w-3 h-3 text-[#ff7759] animate-spin shrink-0" />}
                  {state === 'failed' && <XCircle className="w-3 h-3 text-[#b30000] shrink-0" />}
                  {state === 'pending' && <div className="w-1.5 h-1.5 rounded-full bg-[#3a3a48] shrink-0" />}
                  <span className="mono-label text-[9px] leading-tight truncate">{step.label}</span>
                </div>
              );
            })}
          </div>

          {/* Extraction Metrics */}
          {(status.extracted_entities_count !== undefined || status.extracted_relationships_count !== undefined) && (
            <div className="flex gap-4 pt-2 text-[10px] border-t border-[#2a2a35] text-[#93939f]">
              <div>
                ENTITIES:&nbsp;
                <span className="text-white font-mono font-bold">{status.extracted_entities_count || 0}</span>
              </div>
              <div>
                RELATIONSHIPS:&nbsp;
                <span className="text-white font-mono font-bold">{status.extracted_relationships_count || 0}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// --------------------------------------------------------------------------
//  Container that renders one IngestionProgressItem per active document
// --------------------------------------------------------------------------

interface IngestionProgressListProps {
  activeDocumentIds: string[];
}

export function IngestionProgressList({ activeDocumentIds }: IngestionProgressListProps) {
  if (activeDocumentIds.length === 0) return null;

  return (
    <div className="bg-[#17171c] text-white rounded-[22px] p-6 border border-[#212121]">
      <div className="flex items-center justify-between pb-4 border-b border-[#33333e] mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-[#ff7759]" />
          <span className="mono-label text-white">LIVE INGESTION STATUS</span>
        </div>
        <span className="mono-label text-xs text-[#93939f]">
          {activeDocumentIds.length} DOCUMENT{activeDocumentIds.length > 1 ? 'S' : ''} IN PIPELINE
        </span>
      </div>

      <div className="space-y-3">
        {activeDocumentIds.map((id) => (
          <IngestionProgressItem key={id} documentId={id} />
        ))}
      </div>
    </div>
  );
}
