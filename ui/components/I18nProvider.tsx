'use client';

import { ReactNode, useEffect, useState } from 'react';
import { I18nextProvider } from 'react-i18next';
import i18next from 'i18next';
import Backend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';
import { languages } from '@/lib/i18n';

// We'll add default translations in case loading fails
const fallbackTranslations = {
  en: {
    translation: {
      'app.title': 'KAI',
      'app.description': 'Your AI Assistant',
      'common.loading': 'Loading...'
    }
  }
};

// Initialize i18next
i18next
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    supportedLngs: languages.map(lang => lang.code),
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',
    defaultNS: 'translation',
    interpolation: {
      escapeValue: false // React already escapes values
    },
    detection: {
      order: ['path', 'localStorage', 'navigator'],
      lookupFromPathIndex: 0,
      caches: ['localStorage']
    },
    backend: {
      // Use absolute path with public prefix to ensure it works
      loadPath: '/locales/{{lng}}/{{ns}}.json',
      // Force no caching during development
      requestOptions: {
        cache: 'no-store',
        mode: 'cors',
        credentials: 'same-origin',
      }
    },
    react: {
      useSuspense: false,
    },
    resources: fallbackTranslations // Add fallback translations
  });

interface I18nProviderProps {
  children: ReactNode;
}

/**
 * Provider component that wraps the app to provide i18n context
 */
export function I18nProvider({ children }: I18nProviderProps) {
  const [isI18nInitialized, setIsI18nInitialized] = useState(false);

  useEffect(() => {
    const initI18n = async () => {
      try {
        // Get language from URL path
        const path = window.location.pathname;
        const langMatch = path.match(/^\/([a-z]{2})(\/|$)/);
        const lang = langMatch ? langMatch[1] : 'en';
        
        console.log(`Setting language to ${lang} from path ${path}`);
        
        // Pre-load the translations directly from public path
        // This avoids the 404 error when i18next tries to load them
        try {
          // Ensure we're using the correct public path to the locales
          const loadPath = `/locales/${lang}/translation.json`;
          console.log(`Loading translations from: ${loadPath}`);
          
          // Add a cache-busting query parameter
          const response = await fetch(`${loadPath}?t=${Date.now()}`, {
            cache: 'no-store',
            headers: {
              'Accept': 'application/json',
              'Cache-Control': 'no-cache'
            }
          });
          
          if (!response.ok) {
            throw new Error(`Failed to load ${lang} translations: ${response.status}`);
          }
          
          const data = await response.json();
          console.log(`Loaded translations for ${lang}:`, data);
          
          // Add translations manually to i18next
          i18next.addResourceBundle(lang, 'translation', data, true, true);
        } catch (error) {
          console.error(`Error loading translations manually, using fallbacks:`, error);
        }
        
        // Change the language
        await i18next.changeLanguage(lang);
        setIsI18nInitialized(true);
      } catch (error) {
        console.error('Failed to initialize i18n:', error);
        setIsI18nInitialized(true); // Still render children even if i18n fails
      }
    };
    
    // Only run on client side
    if (typeof window !== 'undefined') {
      initI18n();
    } else {
      setIsI18nInitialized(true);
    }
  }, []);

  // Show loading state until initialized
  if (!isI18nInitialized) {
    return <div className="loading">Loading translations...</div>;
  }

  return (
    <I18nextProvider i18n={i18next}>
      {children}
    </I18nextProvider>
  );
} 