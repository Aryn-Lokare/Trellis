'use client';

import React, { useState } from 'react';
import { QuestionInputForm } from '../../components/chat/QuestionInputForm';
import { ChatMessageBubble } from '../../components/chat/ChatMessageBubble';
import { useQuerySubmission } from '../../hooks/useQuery';
import { QueryResponse } from '../../types';
import { MessageSquareText, Loader2, ArrowRight } from 'lucide-react';
import Link from 'next/link';
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

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="border-b border-[#d9d9dd] pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <span className="mono-label text-[#1863dc]">STEP 2 OF 3 • CITED RAG INVESTIGATION</span>
          <h1 className="text-4xl sm:text-5xl font-medium tracking-tight text-[#17171c] mt-1">
            Investigate Compliance Queries
          </h1>
          <p className="text-base text-[#616161] max-w-2xl mt-2">
            Ask natural-language questions across ingested call recordings, PDFs, compliance tables, and schematics. Every claim is cited back to exact document spans (page numbers or timestamps).
          </p>
        </div>

        <Link href="/graph" className="button-pill-outline inline-flex items-center gap-2 mono-label text-[11px] shrink-0 self-start md:self-auto">
          <span>Visualize Full Subgraph</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Question Form */}
      <div className="bg-[#eeece7] border border-[#d9d9dd] rounded-[8px] p-6">
        <QuestionInputForm onSubmit={handleQuerySubmit} isLoading={queryMutation.isPending} />
      </div>

      {/* Query Loading State */}
      {queryMutation.isPending && (
        <div className="bg-[#17171c] text-white rounded-[22px] p-8 border border-[#212121] text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-[#ff7759]/20 text-[#ff7759] flex items-center justify-center mx-auto">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
          <div>
            <span className="mono-label text-xs text-[#ffad9b]">GRAPHRAG REASONING IN PROGRESS</span>
            <h3 className="text-xl font-medium text-white mt-1">
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

      {/* Empty State before any question is asked */}
      {history.length === 0 && !queryMutation.isPending && !queryMutation.isError && (
        <div className="agent-console-card py-16 text-center p-8">
          <MessageSquareText className="w-10 h-10 text-[#ff7759] mx-auto mb-4" />
          <span className="mono-label text-[#ffad9b] block text-sm">NO ACTIVE INVESTIGATION</span>
          <p className="text-sm text-white/65 mt-1 max-w-md mx-auto">
            Submit a question above to trigger vector search and knowledge graph traversal across your ingested documents.
          </p>
        </div>
      )}

      {/* Chat History List */}
      <div className="space-y-8">
        {history.map((item) => (
          <ChatMessageBubble key={item.id} question={item.question} response={item.response} />
        ))}
      </div>
    </div>
  );
}
