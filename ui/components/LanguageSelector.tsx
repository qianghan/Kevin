'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useI18n } from '@/hooks/useI18n';

// Import UI components
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export function LanguageSelector() {
  const { t, currentLanguage, languages, changeLanguage } = useI18n();
  const pathname = usePathname() || '/';
  
  return (
    <div className="language-selector">
      {/* Mobile dropdown */}
      <div className="md:hidden">
        <Select
          value={currentLanguage}
          onValueChange={changeLanguage}
        >
          <SelectTrigger className="w-[120px]">
            <SelectValue placeholder={t('language.select', 'Select language')} />
          </SelectTrigger>
          <SelectContent>
            {languages.map((lang) => (
              <SelectItem key={lang.code} value={lang.code}>
                {lang.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      {/* Desktop links */}
      <div className="hidden md:flex space-x-2">
        {languages.map((lang) => {
          // Make sure to handle potential null pathname
          const href = pathname 
            ? pathname.replace(`/${currentLanguage}`, `/${lang.code}`)
            : `/${lang.code}`;
            
          return (
            <Link
              key={lang.code}
              href={href}
              locale={lang.code}
              className={`px-2 py-1 rounded-md text-sm ${
                currentLanguage === lang.code
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              }`}
            >
              {lang.code.toUpperCase()}
            </Link>
          );
        })}
      </div>
    </div>
  );
} 