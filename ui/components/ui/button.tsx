'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

/**
 * Reusable button component with different variants and sizes
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(
          'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
          
          // Variants
          variant === 'default' && 'bg-blue-600 text-white hover:bg-blue-700',
          variant === 'destructive' && 'bg-red-600 text-white hover:bg-red-700',
          variant === 'outline' && 'border border-gray-300 bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800',
          variant === 'secondary' && 'bg-gray-200 text-gray-900 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100',
          variant === 'ghost' && 'hover:bg-gray-100 dark:hover:bg-gray-800 bg-transparent',
          variant === 'link' && 'bg-transparent underline-offset-4 hover:underline text-blue-600 dark:text-blue-400',
          
          // Sizes
          size === 'default' && 'h-10 py-2 px-4',
          size === 'sm' && 'h-8 px-3 text-sm',
          size === 'lg' && 'h-12 px-8 text-lg',
          size === 'icon' && 'h-10 w-10',
          
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
); 