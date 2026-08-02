'use client';

import React, { useState } from 'react';
import { Sparkles, Loader2, ArrowRight } from 'lucide-react';
import { Button } from '../ui/button';

interface QuestionInputFormProps {
  onSubmit: (question: string) => void;
  isLoading: boolean;
}

export function QuestionInputForm({ onSubmit, isLoading }: QuestionInputFormProps) {
  const [question, setQuestion] = useState('');

  const sampleQuestions = [
    'Which vendor mentioned in this call recording has a flagged relationship in the compliance table, and what regulation does that violate?',
    'Identify all non-compliant third-party systems referenced in the architectural schematic and their associated risk ratings.',
    'What regulatory frameworks apply to the data retention policies outlined in the uploaded PDF and CSV tables?',
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;
    onSubmit(question.trim());
  };

  const handleSampleClick = (sample: string) => {
    setQuestion(sample);
    onSubmit(sample);
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center bg-white rounded-[22px] border border-[#d9d9dd] p-2 transition-all focus-within:border-[#1863dc] focus-within:ring-2 focus-within:ring-[#1863dc]/20">
          <div className="pl-4 pr-2 text-[#ff7759]">
            <Sparkles className="w-5 h-5" />
          </div>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a compliance question spanning call recordings, PDFs, tables & schematics..."
            disabled={isLoading}
            className="flex-1 py-3 px-2 text-base text-[#212121] bg-transparent border-none outline-none placeholder:text-[#93939f] font-sans"
          />
          <Button
            type="submit"
            disabled={!question.trim() || isLoading}
            variant="primary"
            size="md"
            className="shrink-0"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Searching Graph...</span>
              </>
            ) : (
              <>
                <span>Investigate</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </Button>
        </div>
      </form>

      {/* Suggested Hackathon Demo Questions */}
      <div className="space-y-2">
        <span className="mono-label text-[11px] text-[#93939f] block">
          SUGGESTED CROSS-DOCUMENT COMPLIANCE QUERIES:
        </span>
        <div className="border-y border-[#d9d9dd] divide-y divide-[#d9d9dd]">
          {sampleQuestions.map((sq, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSampleClick(sq)}
              disabled={isLoading}
              className="w-full text-left text-xs text-[#212121] py-3 transition-colors hover:text-[#1863dc] cursor-pointer"
            >
              <span className="font-mono font-bold text-[#ff7759] mr-1.5">Q{idx + 1}.</span>
              {sq}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
