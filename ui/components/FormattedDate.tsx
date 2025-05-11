'use client';

import { useI18n } from '@/hooks/useI18n';

interface FormattedDateProps {
  date: Date;
  format?: Intl.DateTimeFormatOptions;
  className?: string;
}

/**
 * Component for displaying dates formatted according to the current locale
 */
export function FormattedDate({ date, format, className }: FormattedDateProps) {
  const { formatDate } = useI18n();
  
  return (
    <span className={className}>
      {formatDate(date, format)}
    </span>
  );
} 