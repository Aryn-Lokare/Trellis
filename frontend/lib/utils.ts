import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr?: string): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

export function getFileExtension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() || '';
}

export function inferDocumentType(filename: string): 'pdf' | 'audio' | 'table' | 'schematic' {
  const ext = getFileExtension(filename);
  if (['mp3', 'wav', 'm4a', 'ogg', 'aac', 'flac'].includes(ext)) return 'audio';
  if (['csv', 'xlsx', 'xls', 'tsv'].includes(ext)) return 'table';
  if (['png', 'jpg', 'jpeg', 'svg', 'dwg', 'webp', 'cad'].includes(ext)) return 'schematic';
  return 'pdf';
}
