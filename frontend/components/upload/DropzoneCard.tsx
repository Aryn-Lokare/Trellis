'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, Music, Table, Image as ImageIcon, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { DocumentType } from '../../types';
import { inferDocumentType } from '../../lib/utils';
import { InlineState } from '../ui/InlineState';

interface FileEntry {
  id: string;
  file: File;
  type: DocumentType;
}

interface DropzoneCardProps {
  onUpload: (files: FileEntry[]) => Promise<void>;
  isUploading: boolean;
  uploadError: string | null;
}

export function DropzoneCard({ onUpload, isUploading, uploadError }: DropzoneCardProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<FileEntry[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addFiles = (fileList: FileList) => {
    const newEntries: FileEntry[] = Array.from(fileList).map((file) => ({
      id: `${file.name}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      file,
      type: inferDocumentType(file.name),
    }));
    setSelectedFiles((prev) => [...prev, ...newEntries]);
  };

  const removeFile = (id: string) => {
    setSelectedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const updateFileType = (id: string, newType: DocumentType) => {
    setSelectedFiles((prev) =>
      prev.map((f) => (f.id === id ? { ...f, type: newType } : f))
    );
  };

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
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
    }
    // Reset so the same file(s) can be re-selected
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFiles.length === 0) return;
    await onUpload(selectedFiles);
    setSelectedFiles([]);
  };

  const docTypeOptions: { type: DocumentType; label: string; icon: React.ElementType }[] = [
    { type: 'pdf', label: 'PDF', icon: FileText },
    { type: 'audio', label: 'Audio', icon: Music },
    { type: 'table', label: 'Table', icon: Table },
    { type: 'schematic', label: 'Image', icon: ImageIcon },
  ];

  const typeIcon = (t: DocumentType) => {
    const match = docTypeOptions.find((o) => o.type === t);
    return match ? match.icon : FileText;
  };

  return (
    <div className="bg-white border border-[#d9d9dd] rounded-[22px] p-6 sm:p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <span className="mono-label text-[#ff7759]">INGESTION PIPELINE</span>
          <h2 className="text-2xl font-medium tracking-tight text-[#212121] mt-1">
            Upload Mixed-Format Evidence
          </h2>
          <p className="text-sm text-[#93939f] mt-1">
            Drag multiple files at once — PDFs, call recordings, compliance tables, and schematics are auto-detected.
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
          className={`border-2 border-dashed rounded-[22px] p-8 text-center transition-all cursor-pointer flex flex-col items-center justify-center min-h-[180px] ${
            dragActive
              ? 'border-[#1863dc] bg-[#f1f5ff]'
              : selectedFiles.length > 0
              ? 'border-[#003c33] bg-[#edfce9]/30'
              : 'border-[#d9d9dd] bg-[#eeece7]/30 hover:bg-[#eeece7]/60'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileChange}
            accept=".pdf,.mp3,.wav,.m4a,.csv,.xlsx,.tsv,.png,.jpg,.jpeg,.svg"
            className="hidden"
          />

          <div className="w-12 h-12 rounded-full bg-[#17171c] text-white flex items-center justify-center mb-4">
            <Upload className="w-6 h-6 text-[#ff7759]" />
          </div>

          {selectedFiles.length > 0 ? (
            <div className="space-y-1">
              <span className="mono-label text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded">
                {selectedFiles.length} FILE{selectedFiles.length > 1 ? 'S' : ''} SELECTED
              </span>
              <p className="text-xs text-[#93939f] mt-1">Click or drag to add more</p>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-base font-medium text-[#212121]">
                Drag and drop your files here, or <span className="text-[#1863dc] underline">browse</span>
              </p>
              <p className="text-xs text-[#93939f]">
                Supports PDF, MP3/WAV Audio, CSV/XLSX Tables, and PNG/JPG Schematics — multiple files at once
              </p>
            </div>
          )}
        </div>

        {/* Selected files list with per-file type controls */}
        {selectedFiles.length > 0 && (
          <div className="mt-6 pt-4 border-t border-[#d9d9dd] space-y-3">
            <label className="mono-label text-[#212121] block">
              {selectedFiles.length} FILE{selectedFiles.length > 1 ? 'S' : ''} READY FOR EXTRACTION:
            </label>

            <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
              {selectedFiles.map((entry) => {
                const Icon = typeIcon(entry.type);
                return (
                  <div
                    key={entry.id}
                    className="flex items-center gap-3 bg-[#eeece7]/50 border border-[#d9d9dd] rounded-[12px] p-3"
                  >
                    {/* Icon */}
                    <div className="w-8 h-8 rounded-[6px] bg-[#17171c] text-[#ff7759] flex items-center justify-center shrink-0">
                      <Icon className="w-4 h-4" />
                    </div>

                    {/* Name & size */}
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-[#212121] truncate">{entry.file.name}</p>
                      <p className="text-[10px] text-[#93939f] font-mono">
                        {(entry.file.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>

                    {/* Type selector */}
                    <select
                      value={entry.type}
                      onChange={(e) => updateFileType(entry.id, e.target.value as DocumentType)}
                      onClick={(e) => e.stopPropagation()}
                      className="text-xs font-mono bg-white border border-[#d9d9dd] rounded-[6px] px-2 py-1.5 text-[#212121] cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#1863dc]"
                    >
                      {docTypeOptions.map((opt) => (
                        <option key={opt.type} value={opt.type}>
                          {opt.label}
                        </option>
                      ))}
                    </select>

                    {/* Remove button */}
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); removeFile(entry.id); }}
                      className="w-7 h-7 rounded-full flex items-center justify-center text-[#93939f] hover:bg-red-50 hover:text-red-500 transition-colors shrink-0"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
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
                {isUploading
                  ? `Ingesting ${selectedFiles.length} Document${selectedFiles.length > 1 ? 's' : ''}...`
                  : `Start Extraction (${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''})`}
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
