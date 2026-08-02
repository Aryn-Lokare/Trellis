'use client';

import React, { useState } from 'react';
import { DropzoneCard } from '../../components/upload/DropzoneCard';
import { IngestionProgressList } from '../../components/upload/IngestionProgressList';
import { DocumentListTable } from '../../components/upload/DocumentListTable';
import { useUpload } from '../../hooks/useUpload';
import { DocumentType } from '../../types';
import { UploadCloud, Database, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function UploadPage() {
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const uploadMutation = useUpload();

  const handleUpload = async (file: File, docType: DocumentType) => {
    try {
      const result = await uploadMutation.mutateAsync({ file, documentType: docType });
      if (result && result.id) {
        setActiveDocumentId(result.id);
      }
    } catch {
      // Error is handled via uploadMutation.error
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Editorial Section Heading */}
      <div className="border-b border-[#d9d9dd] pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <span className="mono-label text-[#ff7759]">STEP 1 OF 3 • MULTI-MODAL INGESTION</span>
          <h1 className="text-4xl sm:text-5xl font-medium tracking-tight text-[#17171c] mt-1">
            Ingest Evidence & Build Graph
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

      {/* Primary Ingestion Form */}
      <DropzoneCard
        onUpload={handleUpload}
        isUploading={uploadMutation.isPending}
        uploadError={uploadMutation.error ? uploadMutation.error.message || 'Upload failed. Check backend connection.' : null}
      />

      {/* Live Ingestion Status Bar */}
      <IngestionProgressList activeDocumentId={activeDocumentId} />

      {/* Repository Table */}
      <DocumentListTable />
    </div>
  );
}
