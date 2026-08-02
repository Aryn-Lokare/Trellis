import React from 'react';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function Dialog({ isOpen, onClose, title, children, className }: DialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="fixed inset-0"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        className={cn(
          'relative z-10 w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-white rounded-[22px] border border-[#d9d9dd] p-6 shadow-2xl',
          className
        )}
      >
        <div className="flex items-center justify-between border-b border-[#d9d9dd] pb-4 mb-4">
          {title && <h3 className="text-xl font-medium tracking-tight text-[#212121]">{title}</h3>}
          <button
            onClick={onClose}
            className="p-1.5 text-[#93939f] hover:text-[#17171c] hover:bg-[#eeece7] rounded-full transition-colors cursor-pointer ml-auto"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div>{children}</div>
      </div>
    </div>
  );
}
