'use client';

import React, { useState, useRef } from 'react';
import {
  Upload,
  FileText,
  Music,
  Table,
  Image as ImageIcon,
  X,
  Paperclip,
  Download,
  ExternalLink,
  Mic,
  Play,
  Pause,
  User,
} from 'lucide-react';
import { Button } from '../ui/button';
import { DocumentType } from '../../types';
import { inferDocumentType } from '../../lib/utils';
import { InlineState } from '../ui/InlineState';

// --------------------------------------------------------------------------
//  Types
// --------------------------------------------------------------------------
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

type LocalAttachment =
  | { id: string; kind: 'file'; file: File; name: string; size: number; type: DocumentType }
  | { id: string; kind: 'web'; url: string; name: string };

// --------------------------------------------------------------------------
//  Sub-Components (Attachments Rendering)
// --------------------------------------------------------------------------

// 1. PDF & Table Attachment Row
interface PDFAttachmentRowProps {
  id: string;
  name: string;
  size: number;
  type: DocumentType;
  file?: File;
  onRemove: (id: string) => void;
}

function PDFAttachmentRow({ id, name, size, type, file, onRemove }: PDFAttachmentRowProps) {
  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const mb = bytes / (1024 * 1024);
    if (mb >= 1) return `${mb.toFixed(1)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
  };

  const handleDownload = () => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex items-center justify-between bg-[#f9f9fb] border border-[#eef0f3] rounded-[16px] p-3.5 shadow-sm transition-all hover:border-[#d9d9dd]">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-8 h-8 rounded-full bg-[#f1f2f5] text-[#71717a] flex items-center justify-center shrink-0">
          {type === 'table' ? (
            <Table className="w-4 h-4" />
          ) : (
            <Paperclip className="w-4 h-4" />
          )}
        </div>
        <span className="text-sm font-medium text-[#17171c] truncate">{name}</span>
      </div>

      <div className="flex items-center gap-4 shrink-0">
        <span className="text-xs text-[#71717a] font-medium">{formatSize(size)}</span>
        {file && (
          <button
            type="button"
            onClick={handleDownload}
            className="w-8 h-8 rounded-full flex items-center justify-center text-[#71717a] hover:bg-[#f1f2f5] transition-colors cursor-pointer"
          >
            <Download className="w-4 h-4" />
          </button>
        )}
        <button
          type="button"
          onClick={() => onRemove(id)}
          className="w-8 h-8 rounded-full flex items-center justify-center text-[#93939f] hover:bg-red-50 hover:text-red-500 transition-colors shrink-0 cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// 2. Web URL Attachment Row
interface WebAttachmentRowProps {
  id: string;
  url: string;
  name: string;
  onRemove: (id: string) => void;
}

function WebAttachmentRow({ id, url, name, onRemove }: WebAttachmentRowProps) {
  return (
    <div className="flex items-center justify-between bg-[#f9f9fb] border border-[#eef0f3] rounded-[16px] p-3.5 shadow-sm transition-all hover:border-[#d9d9dd]">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-8 h-8 rounded-full bg-[#f1f2f5] text-[#71717a] flex items-center justify-center shrink-0">
          <Paperclip className="w-4 h-4 rotate-90" />
        </div>
        <span className="text-sm font-medium text-[#17171c] truncate">{name}</span>
      </div>

      <div className="flex items-center gap-4 shrink-0">
        <div className="flex items-center gap-1 text-xs text-[#71717a] font-medium bg-[#f1f2f5] px-2.5 py-1 rounded-md">
          <span>Web</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </div>
        <button
          type="button"
          onClick={() => onRemove(id)}
          className="w-8 h-8 rounded-full flex items-center justify-center text-[#93939f] hover:bg-red-50 hover:text-red-500 transition-colors shrink-0 cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// 3. Audio Waveform Player Row
interface AudioAttachmentRowProps {
  id: string;
  name: string;
  file: File;
  onRemove: (id: string) => void;
}

function AudioAttachmentRow({ id, name, file, onRemove }: AudioAttachmentRowProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  React.useEffect(() => {
    const audio = new Audio();
    const url = URL.createObjectURL(file);
    audio.src = url;
    audioRef.current = audio;

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.pause();
      URL.revokeObjectURL(url);
    };
  }, [file]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().catch((err) => {
        console.error('Audio playback failed:', err);
      });
      setIsPlaying(true);
    }
  };

  const formatTime = (secs: number) => {
    if (isNaN(secs) || secs === 0) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  // Waveform bars
  const totalBars = 35;
  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="flex items-center gap-4 bg-[#f9f9fb] border border-[#eef0f3] rounded-[16px] p-3.5 shadow-sm transition-all hover:border-[#d9d9dd]">
      {/* Icon */}
      <div className="w-8 h-8 rounded-full bg-[#f1f2f5] text-[#71717a] flex items-center justify-center shrink-0">
        <Mic className="w-4 h-4 text-[#71717a]" />
      </div>

      {/* Time */}
      <span className="text-xs font-mono text-[#71717a] shrink-0 min-w-[28px] text-right">
        {formatTime(currentTime)}
      </span>

      {/* Waveform */}
      <div className="flex-1 flex items-center justify-between gap-[2px] h-6 px-1">
        {Array.from({ length: totalBars }).map((_, idx) => {
          const barPercent = (idx / totalBars) * 100;
          const isActive = barPercent <= progressPercent;
          const heights = [
            12, 16, 8, 20, 14, 24, 18, 10, 14, 16, 22, 12, 8, 14, 18, 10, 16, 20, 12, 14, 22, 10,
            8, 16, 18, 14, 20, 12, 16, 8, 10, 14, 16, 12, 8,
          ];
          const height = heights[idx % heights.length];
          return (
            <div
              key={idx}
              className="w-[3px] rounded-full transition-colors duration-150"
              style={{
                height: `${height}px`,
                backgroundColor: isActive ? '#17171c' : '#e4e4e7',
              }}
            />
          );
        })}
      </div>

      {/* Duration */}
      <span className="text-xs font-mono text-[#71717a] shrink-0 min-w-[28px]">
        {formatTime(duration || 48)}
      </span>

      {/* Play/Pause Button */}
      <button
        type="button"
        onClick={togglePlay}
        className="w-8 h-8 rounded-full bg-[#17171c] hover:bg-black text-white flex items-center justify-center shrink-0 transition-all hover:scale-105 active:scale-95 cursor-pointer"
      >
        {isPlaying ? (
          <Pause className="w-3.5 h-3.5 fill-white text-white" />
        ) : (
          <Play className="w-3.5 h-3.5 fill-white text-white ml-0.5" />
        )}
      </button>

      {/* Remove Button */}
      <button
        type="button"
        onClick={() => onRemove(id)}
        className="w-8 h-8 rounded-full flex items-center justify-center text-[#93939f] hover:bg-red-50 hover:text-red-500 transition-colors shrink-0 cursor-pointer"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

// 4. Image Grid Gallery Component
interface ImageGridProps {
  images: Array<{
    id: string;
    file: File;
    size: number;
  }>;
  onRemove: (id: string) => void;
  onAddMore: () => void;
}

function ImageGrid({ images, onRemove, onAddMore }: ImageGridProps) {
  const [previews, setPreviews] = useState<Record<string, string>>({});

  React.useEffect(() => {
    const newPreviews: Record<string, string> = {};
    images.forEach((img) => {
      newPreviews[img.id] = URL.createObjectURL(img.file);
    });
    setPreviews(newPreviews);

    return () => {
      Object.values(newPreviews).forEach((url) => URL.revokeObjectURL(url));
    };
  }, [images]);

  const formatSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    if (mb >= 1) return `${mb.toFixed(0)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 gap-4">
      {images.map((img) => (
        <div
          key={img.id}
          className="relative aspect-[3/2] bg-[#f1f2f5] border border-[#eef0f3] rounded-[16px] overflow-hidden group shadow-sm transition-all hover:border-[#d9d9dd]"
        >
          {previews[img.id] ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={previews[img.id]} alt="Thumbnail preview" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-[#93939f]">
              <ImageIcon className="w-6 h-6" />
            </div>
          )}

          {/* Close button at top-left */}
          <button
            type="button"
            onClick={() => onRemove(img.id)}
            className="absolute top-2 left-2 w-6 h-6 rounded-full bg-white/95 hover:bg-red-50 text-gray-500 hover:text-red-500 flex items-center justify-center shadow-md transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>

          {/* Size badge at bottom-left */}
          <div className="absolute bottom-2 left-2 bg-black/60 backdrop-blur-[2px] text-white text-[10px] font-mono px-2 py-0.5 rounded-[6px] font-semibold">
            {formatSize(img.size)}
          </div>
        </div>
      ))}

      {/* Plus card at the end */}
      <button
        type="button"
        onClick={onAddMore}
        className="relative aspect-[3/2] bg-[#f1f2f5]/60 hover:bg-[#f1f2f5] border border-dashed border-[#d9d9dd] hover:border-gray-400 rounded-[16px] flex items-center justify-center transition-all cursor-pointer group shadow-sm"
      >
        <div className="flex flex-col items-center justify-center gap-1 text-[#71717a] group-hover:scale-110 transition-transform">
          <span className="text-2xl font-light">+</span>
        </div>
      </button>
    </div>
  );
}

// --------------------------------------------------------------------------
//  Main Component
// --------------------------------------------------------------------------
export function DropzoneCard({ onUpload, isUploading, uploadError }: DropzoneCardProps) {
  const [dragActive, setDragActive] = useState(false);
  const [attachments, setAttachments] = useState<LocalAttachment[]>([]);
  const [showWebInput, setShowWebInput] = useState(false);
  const [webUrl, setWebUrl] = useState('');
  const [tags, setTags] = useState<string[]>(['@xchyler', '@smintify', '@elonmusk', '@fervor']);
  const [newTag, setNewTag] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addFiles = (fileList: FileList) => {
    const newEntries: LocalAttachment[] = Array.from(fileList).map((file) => ({
      id: `${file.name}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      kind: 'file',
      file,
      name: file.name,
      size: file.size,
      type: inferDocumentType(file.name),
    }));
    setAttachments((prev) => [...prev, ...newEntries]);
  };

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
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
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleAddWebUrl = (e: React.FormEvent) => {
    e.preventDefault();
    if (!webUrl.trim()) return;

    let name = webUrl.trim();
    try {
      const urlWithProto = webUrl.match(/^https?:\/\//) ? webUrl : `https://${webUrl}`;
      const urlObj = new URL(urlWithProto);
      name = urlObj.hostname + urlObj.pathname;
      if (name.endsWith('/')) name = name.slice(0, -1);
    } catch {
      // Keep name as webUrl
    }

    const newEntry: LocalAttachment = {
      id: `web-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      kind: 'web',
      url: webUrl.trim(),
      name: name,
    };

    setAttachments((prev) => [...prev, newEntry]);
    setWebUrl('');
    setShowWebInput(false);
  };

  const handleAddTag = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTag.trim()) return;
    let formatted = newTag.trim();
    if (!formatted.startsWith('@')) {
      formatted = `@${formatted}`;
    }
    if (!tags.includes(formatted)) {
      setTags((prev) => [...prev, formatted]);
    }
    setNewTag('');
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags((prev) => prev.filter((t) => t !== tagToRemove));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (attachments.length === 0) return;

    const filesToUpload: FileEntry[] = attachments.map((att) => {
      if (att.kind === 'file') {
        return {
          id: att.id,
          file: att.file,
          type: att.type,
        };
      } else {
        const mockFile = new File([att.url], att.name, { type: 'text/plain' });
        return {
          id: att.id,
          file: mockFile,
          type: 'pdf',
        };
      }
    });

    await onUpload(filesToUpload);
    setAttachments([]);
  };

  const fileRows = attachments.filter(
    (att) => att.kind === 'web' || (att.kind === 'file' && att.type !== 'schematic')
  );

  const imageGridFiles = attachments
    .filter(
      (att): att is { id: string; kind: 'file'; file: File; name: string; size: number; type: DocumentType } =>
        att.kind === 'file' && att.type === 'schematic'
    )
    .map((att) => ({ id: att.id, file: att.file, size: att.size }));

  return (
    <div className="bg-white border border-[#d9d9dd] rounded-[22px] p-6 sm:p-8 space-y-6">
      {/* Redesigned Drag & Drop Area */}
      <div>
        <div
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border border-dashed rounded-[20px] p-8 text-center transition-all cursor-pointer flex flex-col items-center justify-center min-h-[180px] bg-[#fdfdfd] hover:bg-gray-50/50 ${
            dragActive ? 'border-[#1863dc] bg-[#f1f5ff]' : 'border-[#d9d9dd]'
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

          <div className="w-10 h-10 rounded-full flex items-center justify-center mb-3">
            <svg
              className="w-6 h-6 text-[#71717a]"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="2"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5h10.5" />
            </svg>
          </div>

          <p className="text-sm font-medium text-[#17171c]">
            Drop and drop or{' '}
            <span
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
              className="text-[#1863dc] hover:underline cursor-pointer font-semibold"
            >
              browse files
            </span>
          </p>
          <p className="text-xs text-[#93939f] mt-1.5 font-medium">Maximum 500 MB file size</p>
        </div>

        {/* Link / Web input toggle */}
        <div className="mt-3 flex justify-end">
          {!showWebInput ? (
            <button
              type="button"
              onClick={() => setShowWebInput(true)}
              className="text-xs font-semibold text-[#1863dc] hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span className="text-sm font-bold">+</span> Add Website URL
            </button>
          ) : (
            <form
              onSubmit={handleAddWebUrl}
              className="w-full flex gap-2 animate-in fade-in slide-in-from-top-1 duration-200"
            >
              <input
                type="text"
                placeholder="Enter website URL (e.g. example.com)..."
                value={webUrl}
                onChange={(e) => setWebUrl(e.target.value)}
                className="flex-1 text-sm bg-white border border-[#d9d9dd] rounded-lg px-3 py-2 text-[#212121] focus:outline-none focus:ring-1 focus:ring-[#1863dc]"
              />
              <Button type="submit" size="sm" variant="secondary">
                Add URL
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => {
                  setShowWebInput(false);
                  setWebUrl('');
                }}
              >
                Cancel
              </Button>
            </form>
          )}
        </div>
      </div>

      {/* Attachments Section */}
      {attachments.length > 0 && (
        <div className="space-y-4 pt-4 border-t border-[#f1f2f5]">
          <h3 className="text-sm font-semibold text-[#71717a]">Attachments:</h3>

          {/* List of Non-image attachments */}
          {fileRows.length > 0 && (
            <div className="space-y-3">
              {fileRows.map((att) => {
                if (att.kind === 'web') {
                  return (
                    <WebAttachmentRow
                      key={att.id}
                      id={att.id}
                      url={att.url}
                      name={att.name}
                      onRemove={removeAttachment}
                    />
                  );
                } else if (att.type === 'audio') {
                  return (
                    <AudioAttachmentRow
                      key={att.id}
                      id={att.id}
                      name={att.name}
                      file={att.file}
                      onRemove={removeAttachment}
                    />
                  );
                } else {
                  return (
                    <PDFAttachmentRow
                      key={att.id}
                      id={att.id}
                      name={att.name}
                      size={att.size}
                      type={att.type}
                      file={att.file}
                      onRemove={removeAttachment}
                    />
                  );
                }
              })}
            </div>
          )}

          {/* Image/Schematic Grid */}
          {imageGridFiles.length > 0 && (
            <div className="space-y-3 pt-2">
              <ImageGrid
                images={imageGridFiles}
                onRemove={removeAttachment}
                onAddMore={() => fileInputRef.current?.click()}
              />
            </div>
          )}
        </div>
      )}

      {/* Profile Chips/Tags Section */}
      <div className="pt-4 border-t border-[#f1f2f5] space-y-3">
        <div className="flex items-center justify-between">
          <label className="mono-label text-[#71717a] font-semibold block">Assignees &amp; Tags:</label>
          <form onSubmit={handleAddTag} className="flex gap-1.5">
            <input
              type="text"
              placeholder="Add tag (e.g. @username)..."
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              className="text-xs bg-white border border-[#d9d9dd] rounded-lg px-2.5 py-1.5 text-[#212121] focus:outline-none focus:ring-1 focus:ring-[#1863dc]"
            />
            <button
              type="submit"
              className="text-xs font-semibold bg-[#17171c] hover:bg-black text-white px-3 py-1.5 rounded-lg cursor-pointer transition-colors"
            >
              Add
            </button>
          </form>
        </div>

        <div className="flex flex-wrap gap-2.5">
          {tags.map((tag) => (
            <div
              key={tag}
              className="inline-flex items-center gap-2 bg-[#f9f9fb] border border-[#eef0f3] rounded-full pl-1.5 pr-2.5 py-1 text-xs text-[#17171c] font-medium shadow-sm transition-all hover:bg-[#f1f2f5] hover:border-[#d9d9dd]"
            >
              <div className="w-5 h-5 rounded-full bg-white border border-[#eef0f3] flex items-center justify-center shrink-0">
                <User className="w-3 h-3 text-[#93939f]" />
              </div>
              <span>{tag}</span>
              <button
                type="button"
                onClick={() => handleRemoveTag(tag)}
                className="w-4 h-4 rounded-full flex items-center justify-center text-[#71717a] hover:bg-red-50 hover:text-red-500 transition-colors ml-0.5 cursor-pointer"
              >
                <X className="w-2.5 h-2.5" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Start Extraction Submit Action */}
      {attachments.length > 0 && (
        <div className="flex justify-end pt-2">
          <Button
            onClick={handleSubmit}
            disabled={isUploading}
            variant="primary"
            size="lg"
            className="w-full sm:w-auto"
          >
            {isUploading
              ? `Ingesting ${attachments.length} Document${attachments.length > 1 ? 's' : ''}...`
              : `Start Extraction (${attachments.length} item${attachments.length > 1 ? 's' : ''})`}
          </Button>
        </div>
      )}

      {/* Error Banner */}
      {uploadError && <InlineState label="Failed to upload document" cause={uploadError} className="mt-4" />}
    </div>
  );
}
