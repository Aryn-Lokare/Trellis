'use client';

import React, { useState } from 'react';
import { QuestionInputForm } from '../../components/chat/QuestionInputForm';
import { ChatMessageBubble } from '../../components/chat/ChatMessageBubble';
import { useQuerySubmission } from '../../hooks/useQuery';
import { QueryResponse } from '../../types';
import { 
  MessageSquareText, 
  Loader2, 
  ArrowRight, 
  RefreshCw, 
  Volume2, 
  Network, 
  FileText, 
  Table 
} from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { InlineState } from '../../components/ui/InlineState';

interface ChatHistoryItem {
  id: string;
  question: string;
  response: QueryResponse;
}

export default function ChatPage() {
  const [history, setHistory] = useState<ChatHistoryItem[]>([]);
  const [activeQuestion, setActiveQuestion] = useState<string>('');
  const queryMutation = useQuerySubmission();

  const handleQuerySubmit = async (question: string) => {
    setActiveQuestion(question);
    try {
      const response = await queryMutation.mutateAsync(question);
      if (response) {
        setHistory((prev) => [
          ...prev,
          {
            id: `query-${Date.now()}`,
            question,
            response,
          },
        ]);
      }
    } catch {
      // Error handled via queryMutation.isError
    }
  };

  const sampleSuggestions = [
    {
      title: 'Analyze Vendor Compliance',
      description: 'Cross-reference call recordings with compliance tables for regulatory violations.',
      question: 'Which vendor mentioned in this call recording has a flagged relationship in the compliance table, and what regulation does that violate?',
      icon: Volume2,
    },
    {
      title: 'Identify System Risks',
      description: 'Scan architectural schematics for non-compliant third-party integrations.',
      question: 'Identify all non-compliant third-party systems referenced in the architectural schematic and their associated risk ratings.',
      icon: Network,
    },
    {
      title: 'Verify Data Retention',
      description: 'Check data retention policies in PDFs and CSV tables against regulations.',
      question: 'What regulatory frameworks apply to the data retention policies outlined in the uploaded PDF and CSV tables?',
      icon: FileText,
    },
    {
      title: 'Audit Vendor Invoices',
      description: 'Check CSV invoices against payment terms in the signed agreement PDF.',
      question: 'Check the latest vendor invoices in the CSV against the payment terms in the signed agreement PDF.',
      icon: Table,
    },
  ];

  // Landing view when no questions have been asked yet
  if (history.length === 0 && !queryMutation.isPending && !queryMutation.isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-14rem)] max-w-3xl mx-auto px-4 py-8 space-y-10 animate-in fade-in duration-300">

        {/* Headline */}
        <h1 className="text-3xl sm:text-4xl font-medium tracking-tight text-[#17171c] font-display text-center">
          Investigate Compliance Queries
        </h1>

        {/* Input bar capsule */}
        <div className="w-full">
          <QuestionInputForm onSubmit={handleQuerySubmit} isLoading={queryMutation.isPending} layout="landing" />
        </div>

        {/* 2x2 Suggestion Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full pt-2">
          {sampleSuggestions.map((suggestion, idx) => {
            const IconComponent = suggestion.icon;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => handleQuerySubmit(suggestion.question)}
                disabled={queryMutation.isPending}
                className="group w-full text-left p-4 bg-white border border-neutral-200/60 rounded-2xl hover:border-neutral-300 hover:bg-neutral-50/50 hover:shadow-sm transition-all duration-200 cursor-pointer flex gap-3.5 items-start active:scale-[0.99]"
              >
                <div className="p-2 rounded-xl bg-neutral-100/80 text-[#ff7759] group-hover:bg-[#ff7759]/10 transition-colors shrink-0">
                  <IconComponent className="w-4.5 h-4.5" />
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="font-semibold text-neutral-800 text-sm group-hover:text-[#17171c] transition-colors leading-tight">
                    {suggestion.title}
                  </span>
                  <span className="text-neutral-500 text-xs mt-1 leading-normal text-ellipsis line-clamp-2">
                    {suggestion.description}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  // Active chat feed view
  return (
    <div className="flex flex-col min-h-[calc(100vh-14rem)] max-w-4xl mx-auto px-4 pb-24 pt-2 animate-in fade-in duration-300 relative">
      {/* Header */}
      <div className="border-b border-[#d9d9dd] pb-4 mb-6 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Image
            src="/logo-black.png"
            alt="Trellis Logo"
            width={100}
            height={32}
            className="object-contain"
            style={{ height: 'auto' }}
          />
          <span className="text-neutral-400">|</span>
          <span className="text-xs font-semibold text-neutral-600 font-mono">INVESTIGATION</span>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/graph" className="button-pill-outline inline-flex items-center gap-1.5 text-[11px]">
            <span>Visualize Full Subgraph</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <button
            onClick={() => {
              setHistory([]);
              setActiveQuestion('');
              queryMutation.reset();
            }}
            className="button-pill-outline bg-neutral-100 hover:bg-neutral-200 text-neutral-800 border-transparent text-[11px] inline-flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Investigation</span>
          </button>
        </div>
      </div>

      {/* Chat History List */}
      <div className="flex-1 space-y-8 pb-10">
        {history.map((item) => (
          <ChatMessageBubble key={item.id} question={item.question} response={item.response} />
        ))}
        
        {/* Query Loading State */}
        {queryMutation.isPending && (
          <div className="bg-[#17171c] text-white rounded-[22px] p-6 sm:p-8 border border-[#212121] text-center space-y-4 animate-pulse">
            <div className="w-12 h-12 rounded-full bg-[#ff7759]/20 text-[#ff7759] flex items-center justify-center mx-auto">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
            <div>
              <span className="mono-label text-xs text-[#ffad9b]">GRAPHRAG REASONING IN PROGRESS</span>
              <h3 className="text-lg font-medium text-white mt-1">
                Traversing Knowledge Subgraph & Verifying Spans...
              </h3>
              <p className="text-xs text-[#93939f] mt-1">
                Analyzing vectors, graph paths, and matching citations across ingested evidence...
              </p>
            </div>
          </div>
        )}

        {/* Query Failure Error State */}
        {queryMutation.isError && (
          <InlineState
            label="Failed to fetch investigation"
            cause={queryMutation.error?.message || 'Could not connect to the backend query endpoint.'}
            onRetry={activeQuestion ? () => handleQuerySubmit(activeQuestion) : undefined}
          />
        )}
      </div>

      {/* Sticky Bottom Input Capsule */}
      <div className="sticky bottom-0 bg-gradient-to-t from-white via-white to-transparent pt-6 pb-4 z-20">
        <div className="max-w-4xl mx-auto">
          <QuestionInputForm onSubmit={handleQuerySubmit} isLoading={queryMutation.isPending} layout="compact" />
        </div>
      </div>
    </div>
  );
}
