'use client';

import { useI18n } from '@/hooks/useI18n';

interface FormattedNumberProps {
  value: number;
  format?: Intl.NumberFormatOptions;
  className?: string;
}

/**
 * Component for displaying numbers formatted according to the current locale
 */
export function FormattedNumber({ value, format, className }: FormattedNumberProps) {
  const { formatNumber } = useI18n();
  
  return (
    <span className={className}>
      {formatNumber(value, format)}
    </span>
  );
} 