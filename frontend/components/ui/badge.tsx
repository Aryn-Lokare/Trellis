import React from 'react';
import { cn } from '../../lib/utils';
import { getEntityTypeColor } from '../../lib/theme';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'outline' | 'solid' | 'coral' | 'stone' | 'entity';
  entityType?: string;
}

export const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'outline', entityType, children, ...props }, ref) => {
    let customStyle: React.CSSProperties = {};

    if (variant === 'entity' && entityType) {
      const color = getEntityTypeColor(entityType);
      customStyle = {
        borderColor: color,
        color: color,
        backgroundColor: `${color}15`,
      };
    }

    const baseStyles =
      'inline-flex items-center font-mono text-[11px] tracking-wider uppercase px-2.5 py-0.5 rounded-[4px] font-medium border transition-colors';

    const variants = {
      outline: 'border-[#d9d9dd] text-[#212121] bg-transparent',
      solid: 'border-[#17171c] text-white bg-[#17171c]',
      coral: 'border-[#ff7759] text-[#ff7759] bg-[#ff7759]/10',
      stone: 'border-[#d9d9dd] text-[#616161] bg-[#eeece7]',
      entity: 'border-[#1863dc] text-[#1863dc] bg-[#1863dc]/10',
    };

    return (
      <div
        ref={ref}
        style={customStyle}
        className={cn(baseStyles, variants[variant], className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Badge.displayName = 'Badge';
