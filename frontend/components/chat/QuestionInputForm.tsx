'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Command, Mic, ArrowUp, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

interface QuestionInputFormProps {
  onSubmit: (question: string) => void;
  isLoading: boolean;
  layout?: 'landing' | 'compact';
  initialValue?: string;
}

export function QuestionInputForm({
  onSubmit,
  isLoading,
  layout = 'landing',
  initialValue = '',
}: QuestionInputFormProps) {
  const [question, setQuestion] = useState(initialValue);
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;
    onSubmit(question.trim());
    setQuestion('');
  };

  const handlePlusClick = () => {
    router.push('/upload');
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div
        className={cn(
          "relative flex items-center bg-[#f4f4f6]/90 backdrop-blur-md border border-neutral-200/80 rounded-full transition-all duration-300",
          "focus-within:border-neutral-300 focus-within:bg-white focus-within:ring-4 focus-within:ring-neutral-200/40 focus-within:shadow-md",
          layout === 'landing' ? 'p-2 sm:p-2.5 shadow-sm' : 'p-1.5 sm:p-2 shadow-sm'
        )}
      >
        {/* Left Side Actions */}
        <div className="flex items-center gap-1 pl-2.5 sm:pl-3">
          {/* Plus Ingest Button */}
          <button
            type="button"
            onClick={handlePlusClick}
            className="group relative flex items-center justify-center w-8 h-8 rounded-full border border-neutral-300/60 bg-white text-neutral-600 hover:text-neutral-900 hover:border-neutral-400 hover:bg-neutral-50 active:scale-95 transition-all cursor-pointer"
            title="Ingest Documents"
          >
            <Plus className="w-4.5 h-4.5" />
            {/* Tooltip */}
            <span className="pointer-events-none absolute -top-10 left-1/2 -translate-x-1/2 scale-0 group-hover:scale-100 transition-all rounded bg-neutral-900 px-2.5 py-1 text-[10px] font-mono tracking-wider text-white whitespace-nowrap shadow-md z-50">
              INGEST DOCUMENTS
            </span>
          </button>
        </div>

        {/* Input Field */}
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask your queries to trellis"
          disabled={isLoading}
          className={cn(
            "flex-1 bg-transparent border-none outline-none text-neutral-800 placeholder:text-neutral-400 font-sans mx-3 sm:mx-4 focus:ring-0 focus:outline-none",
            layout === 'landing' ? 'text-base py-2.5' : 'text-sm py-1.5'
          )}
        />

        {/* Right Side Actions */}
        <div className="flex items-center gap-1.5 pr-1.5">

          {/* Submit Button */}
          {question.trim() ? (
            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                "flex items-center justify-center rounded-full text-white bg-neutral-900 hover:bg-black transition-all active:scale-95 cursor-pointer shadow-sm shrink-0",
                layout === 'landing' ? 'w-9 h-9' : 'w-8 h-8'
              )}
            >
              {isLoading ? (
                <Loader2 className="w-4.5 h-4.5 animate-spin" />
              ) : (
                <ArrowUp className="w-4.5 h-4.5" />
              )}
            </button>
          ) : (
            isLoading && (
              <div className="flex items-center justify-center w-8 h-8 text-neutral-600 shrink-0">
                <Loader2 className="w-4.5 h-4.5 animate-spin" />
              </div>
            )
          )}
        </div>
      </div>
    </form>
  );
}
