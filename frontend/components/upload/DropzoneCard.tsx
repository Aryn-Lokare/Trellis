'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, Music, Table, Image as ImageIcon } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { DocumentType } from '../../types';
import { inferDocumentType } from '../../lib/utils';
import { InlineState } from '../ui/InlineState';

interface DropzoneCardProps {
  onUpload: (file: File, documentType: DocumentType) => Promise<void>;
  isUploading: boolean;
  uploadError: string | null;
}

export function DropzoneCard({ onUpload, isUploading, uploadError }: DropzoneCardProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<DocumentType>('pdf');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setDocType(inferDocumentType(file.name));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setDocType(inferDocumentType(file.name));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    await onUpload(selectedFile, docType);
    setSelectedFile(null);
  };

  const docTypes: { type: DocumentType; label: string; icon: React.ElementType }[] = [
    { type: 'pdf', label: 'PDF Document', icon: FileText },
    { type: 'audio', label: 'Audio Call Recording', icon: Music },
    { type: 'table', label: 'CSV / Compliance Table', icon: Table },
    { type: 'schematic', label: 'Image / Schematic', icon: ImageIcon },
  ];

  return (
    <div className="bg-white border border-[#d9d9dd] rounded-[22px] p-6 sm:p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <span className="mono-label text-[#ff7759]">INGESTION PIPELINE</span>
          <h2 className="text-2xl font-medium tracking-tight text-[#212121] mt-1">
            Upload Mixed-Format Evidence
          </h2>
          <p className="text-sm text-[#93939f] mt-1">
            Ingest PDFs, call recordings, compliance CSV tables, and architectural schematics into the Knowledge Graph.
          </p>
        </div>
      </div>

      {/* Drag & Drop Surface */}
      <form onSubmit={handleSubmit} onDragEnter={handleDrag}>
        <div
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-[22px] p-8 text-center transition-all cursor-pointer flex flex-col items-center justify-center min-h-[220px] ${
            dragActive
              ? 'border-[#1863dc] bg-[#f1f5ff]'
              : selectedFile
              ? 'border-[#003c33] bg-[#edfce9]/30'
              : 'border-[#d9d9dd] bg-[#eeece7]/30 hover:bg-[#eeece7]/60'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.mp3,.wav,.m4a,.csv,.xlsx,.tsv,.png,.jpg,.jpeg,.svg"
            className="hidden"
          />

          <div className="w-12 h-12 rounded-full bg-[#17171c] text-white flex items-center justify-center mb-4">
            <Upload className="w-6 h-6 text-[#ff7759]" />
          </div>

          {selectedFile ? (
            <div className="space-y-2">
              <span className="mono-label text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded">
                FILE SELECTED
              </span>
              <p className="text-base font-medium text-[#212121]">{selectedFile.name}</p>
              <p className="text-xs text-[#93939f]">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Click or drag to replace
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-base font-medium text-[#212121]">
                Drag and drop your file here, or <span className="text-[#1863dc] underline">browse</span>
              </p>
              <p className="text-xs text-[#93939f]">
                Supports PDF, MP3/WAV Audio, CSV/XLSX Tables, and PNG/JPG Schematics
              </p>
            </div>
          )}
        </div>

        {/* File Type Selection */}
        {selectedFile && (
          <div className="mt-6 pt-4 border-t border-[#d9d9dd] space-y-3">
            <label className="mono-label text-[#212121] block">DETECTED DOCUMENT TAXONOMY:</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {docTypes.map((t) => {
                const Icon = t.icon;
                const isSelected = docType === t.type;
                return (
                  <button
                    key={t.type}
                    type="button"
                    onClick={() => setDocType(t.type)}
                    className={`flex items-center gap-2 p-3 rounded-[8px] border text-xs font-mono transition-all text-left ${
                      isSelected
                        ? 'border-[#17171c] bg-[#17171c] text-white font-medium'
                        : 'border-[#d9d9dd] bg-white text-[#616161] hover:bg-[#eeece7]'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isSelected ? 'text-[#ff7759]' : 'text-[#93939f]'}`} />
                    <span className="uppercase">{t.label}</span>
                  </button>
                );
              })}
            </div>

            <div className="flex justify-end mt-4">
              <Button
                type="submit"
                disabled={isUploading}
                variant="primary"
                size="lg"
                className="w-full sm:w-auto"
              >
                {isUploading ? 'Ingesting Document...' : 'Start Knowledge Graph Extraction'}
              </Button>
            </div>
          </div>
        )}
      </form>

      {/* Error Banner */}
      {uploadError && (
        <InlineState label="Failed to upload document" cause={uploadError} className="mt-4" />
      )}
    </div>
  );
}
