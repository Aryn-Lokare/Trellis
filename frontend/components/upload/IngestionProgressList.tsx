'use client';

import React from 'react';
import { Loader2, CheckCircle2, XCircle, Activity } from 'lucide-react';
import { useIngestionStatus } from '../../hooks/useIngestionStatus';
import { Badge } from '../ui/badge';
import { IngestionStepStatus } from '../../types';
import { InlineState } from '../ui/InlineState';

interface IngestionProgressListProps {
  activeDocumentId: string | null;
}

export function IngestionProgressList({ activeDocumentId }: IngestionProgressListProps) {
  const { data: status, isLoading, isError, error, refetch } = useIngestionStatus(activeDocumentId);

  if (!activeDocumentId) return null;

  const steps: { key: IngestionStepStatus; label: string }[] = [
    { key: 'queued', label: '1. Queued for Processing' },
    { key: 'parsing', label: '2. Document Parsing & OCR' },
    { key: 'extracting', label: '3. Entity & Relation Extraction' },
    { key: 'completed', label: '4. Written to Knowledge Graph' },
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
    <div className="bg-[#17171c] text-white rounded-[22px] p-6 border border-[#212121]">
      <div className="flex items-center justify-between pb-4 border-b border-[#33333e] mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-[#ff7759]" />
          <span className="mono-label text-white">LIVE INGESTION STATUS</span>
        </div>
        <span className="mono-label text-xs text-[#93939f]">DOC ID: {activeDocumentId.slice(0, 8)}</span>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8 text-[#93939f] gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-[#1863dc]" />
          <span className="mono-label text-xs">POLLING BACKEND INGESTION PIPELINE...</span>
        </div>
      )}

      {isError && (
        <InlineState
          label="Failed to fetch ingestion status"
          cause={error?.message || 'Failed to fetch status'}
          onRetry={() => refetch()}
          tone="dark"
        />
      )}

      {status && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-[#eeece7]">{status.filename || 'Document'}</span>
            <Badge variant={status.status === 'completed' ? 'solid' : 'coral'}>
              {status.status.toUpperCase()}
            </Badge>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-[#2a2a35] h-2 rounded-full overflow-hidden">
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

          {/* Step Progression Timeline */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 pt-2">
            {steps.map((step) => {
              const state = getStepState(step.key, status.status);
              return (
                <div
                  key={step.key}
                  className={`p-3 rounded-[8px] border text-xs flex items-center gap-2 ${
                    state === 'completed'
                      ? 'border-emerald-900/50 bg-emerald-950/20 text-emerald-400'
                      : state === 'active'
                      ? 'border-[#ff7759] bg-[#ff7759]/10 text-white'
                      : state === 'failed'
                      ? 'border-[#b30000] bg-[#b30000]/20 text-[#b30000]'
                      : 'border-[#2a2a35] bg-[#1c1c24] text-[#75758a]'
                  }`}
                >
                  {state === 'completed' && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
                  {state === 'active' && <Loader2 className="w-4 h-4 text-[#ff7759] animate-spin shrink-0" />}
                  {state === 'failed' && <XCircle className="w-4 h-4 text-[#b30000] shrink-0" />}
                  {state === 'pending' && <div className="w-2 h-2 rounded-full bg-[#3a3a48] shrink-0" />}
                  <span className="mono-label text-[10px] leading-tight">{step.label}</span>
                </div>
              );
            })}
          </div>

          {/* Extraction Metrics */}
          {(status.extracted_entities_count !== undefined || status.extracted_relationships_count !== undefined) && (
            <div className="flex gap-4 pt-2 text-xs border-t border-[#2a2a35] text-[#93939f]">
              <div>
                ENTITIES EXTRACTED: <span className="text-white font-mono font-bold">{status.extracted_entities_count || 0}</span>
              </div>
              <div>
                RELATIONSHIPS LINKED: <span className="text-white font-mono font-bold">{status.extracted_relationships_count || 0}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
