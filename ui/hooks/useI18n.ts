import { useTranslation } from 'react-i18next';
import { useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { languages } from '@/lib/i18n';

/**
 * Custom hook for internationalization functionalities
 */
export function useI18n() {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const pathname = usePathname() || '/';
  
  /**
   * Change the current language
   */
  const changeLanguage = useCallback((langCode: string) => {
    if (!languages.some(lang => lang.code === langCode)) {
      console.error(`Language code "${langCode}" is not supported`);
      return;
    }
    
    const currentLang = i18n.language;
    
    // If language has changed
    if (langCode !== currentLang) {
      // Change language in i18next
      i18n.changeLanguage(langCode);
      
      // Store preference in localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('i18nextLng', langCode);
      }
      
      // Calculate the new path with the selected language
      const path = pathname.replace(`/${currentLang}`, `/${langCode}`);
      
      // Redirect to the same page with new language
      router.push(path);
      router.refresh();
    }
  }, [i18n, router, pathname]);
  
  /**
   * Format a date according to the current locale
   */
  const formatDate = useCallback((date: Date, options?: Intl.DateTimeFormatOptions) => {
    return new Intl.DateTimeFormat(i18n.language, options).format(date);
  }, [i18n.language]);
  
  /**
   * Format a number according to the current locale
   */
  const formatNumber = useCallback((num: number, options?: Intl.NumberFormatOptions) => {
    return new Intl.NumberFormat(i18n.language, options).format(num);
  }, [i18n.language]);
  
  /**
   * Get the current language code
   */
  const currentLanguage = i18n.language;
  
  /**
   * Get the current language name
   */
  const currentLanguageName = languages.find(lang => lang.code === currentLanguage)?.name || 'English';
  
  return {
    t,                  // Translation function
    i18n,               // i18next instance
    currentLanguage,    // Current language code
    currentLanguageName,// Current language name
    languages,          // Available languages
    changeLanguage,     // Change language function
    formatDate,         // Format date according to locale
    formatNumber,       // Format number according to locale
  };
} 