'use client';

import React, { useState } from 'react';
import { DropzoneCard } from '../../components/upload/DropzoneCard';
import { IngestionProgressList } from '../../components/upload/IngestionProgressList';
import { DocumentListTable } from '../../components/upload/DocumentListTable';
import { useUpload } from '../../hooks/useUpload';
import { ArrowRight } from 'lucide-react';
import Link from 'next/link';

interface FileEntry {
  id: string;
  file: File;
  type: string;
}

export default function UploadPage() {
  const [activeDocumentIds, setActiveDocumentIds] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const uploadMutation = useUpload();

  const handleUpload = async (files: FileEntry[]) => {
    setIsUploading(true);
    setUploadError(null);
    const newIds: string[] = [];

    try {
      for (const entry of files) {
        const result = await uploadMutation.mutateAsync({
          file: entry.file,
          documentType: entry.type,
        });
        if (result && result.id) {
          newIds.push(result.id);
        }
      }
      // Append to any existing active IDs (user might upload again while others are processing)
      setActiveDocumentIds((prev) => [...prev, ...newIds]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed. Check backend connection.';
      setUploadError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Editorial Section Heading */}
      <div className="border-b border-[#d9d9dd] pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl sm:text-5xl font-medium tracking-tight text-[#17171c] mt-1">
            Ingest Evidence &amp; Build Graph
          </h1>
          <p className="text-base text-[#616161] max-w-2xl mt-2">
            Upload compliance documents across mixed formats (PDF policy manuals, audio call transcripts, CSV risk matrices, and architectural schematics) to automatically extract entities and relationship triples into the Knowledge Graph.
          </p>
        </div>

        <Link href="/chat" className="button-primary text-xs shrink-0 self-start md:self-auto">
          <span>Proceed to Cited Investigation</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Primary Ingestion Form — now accepts multiple files */}
      <DropzoneCard
        onUpload={handleUpload}
        isUploading={isUploading}
        uploadError={uploadError}
      />

      {/* Live Ingestion Status — renders a progress card per active document */}
      <IngestionProgressList activeDocumentIds={activeDocumentIds} />

      {/* Repository Table */}
      <DocumentListTable />
    </div>
  );
}
