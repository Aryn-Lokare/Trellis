import React from 'react';
import { AlertCircle, type LucideIcon } from 'lucide-react';

interface InlineStateProps {
  label: string;
  cause?: string;
  onRetry?: () => void;
  icon?: LucideIcon;
  tone?: 'light' | 'dark';
  className?: string;
}

/** A contained, honest state for failed live requests. */
export function InlineState({
  label,
  cause,
  onRetry,
  icon: Icon = AlertCircle,
  tone = 'light',
  className = '',
}: InlineStateProps) {
  const isDark = tone === 'dark';

  return (
    <div
      className={`flex items-start gap-3 rounded-[8px] border p-4 ${
        isDark ? 'border-white/20 bg-white/5' : 'border-[#d9d9dd] bg-white/70'
      } ${className}`}
      role="status"
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-[#b30000]" aria-hidden="true" />
      <div className="min-w-0">
        <p className="mono-label text-[11px] text-[#b30000]">{label}</p>
        {cause && <p className={`mt-1 text-xs ${isDark ? 'text-white/65' : 'text-[#616161]'}`}>{cause}</p>}
        {onRetry && (
          <button type="button" onClick={onRetry} className={`button-secondary mt-1 text-xs ${isDark ? '!text-white' : ''}`}>
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
