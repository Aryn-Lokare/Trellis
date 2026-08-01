'use client';

import React from 'react';
import { Citation } from '../../types';
import { CitationChip } from '../citations/CitationChip';

interface InlineCitationTextProps {
  text: string;
  citations: Citation[];
}

export function InlineCitationText({ text, citations }: InlineCitationTextProps) {
  if (!text) return null;

  const regex = /\[(?:Citation\s*)?(\d+)[^\]]*\]/gi;

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    const matchIndex = match.index;
    const fullMatch = match[0];
    const citationNum = parseInt(match[1], 10);

    if (matchIndex > lastIndex) {
      parts.push(text.substring(lastIndex, matchIndex));
    }

    const citation = citations.find(
      (c) => c.citation_index === citationNum || c.id === match![1]
    ) || {
      id: `cit-${citationNum}`,
      citation_index: citationNum,
      source_doc_id: 'unknown',
      source_span: `Citation ${citationNum}`,
      snippet: `Reference marker ${fullMatch}`,
    };

    parts.push(
      <CitationChip key={`cit-${matchIndex}-${citationNum}`} citation={citation} />
    );

    lastIndex = matchIndex + fullMatch.length;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return (
    <div className="leading-relaxed text-sm sm:text-base space-y-3 font-sans">
      {parts.length > 0 ? parts : text}
    </div>
  );
}
