import React from 'react';
import { cn } from '../../lib/utils';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', children, disabled, ...props }, ref) => {
    const baseStyles =
      'inline-flex items-center justify-center font-medium transition-all focus:outline-none focus:ring-2 focus:ring-[#1863dc] disabled:opacity-50 disabled:pointer-events-none cursor-pointer';

    const variants = {
      primary: 'bg-[#17171c] text-white hover:bg-black rounded-full border border-[#17171c]',
      secondary: 'bg-[#eeece7] text-[#212121] hover:bg-[#e2dfd7] rounded-full border border-transparent',
      outline: 'bg-transparent text-[#17171c] border border-[#d9d9dd] hover:bg-[#eeece7] rounded-full',
      ghost: 'bg-transparent text-[#212121] hover:underline p-0 rounded-none',
      danger: 'bg-[#b30000] text-white hover:bg-[#8f0000] rounded-full border border-[#b30000]',
    };

    const sizes = {
      sm: 'text-xs px-3 py-1.5 gap-1.5',
      md: 'text-sm px-5 py-2.5 gap-2',
      lg: 'text-base px-7 py-3.5 gap-2.5',
    };

    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';
