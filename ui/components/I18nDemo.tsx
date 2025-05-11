'use client';

import { useI18n } from '@/hooks/useI18n';
import { LanguageSelector } from './LanguageSelector';

/**
 * Demo component to show the internationalization functionality
 */
export function I18nDemo() {
  const { t, currentLanguage, formatDate, formatNumber } = useI18n();
  const today = new Date();
  const number = 1234567.89;

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">{t('app.title')}</h2>
      <p className="mb-4">{t('app.description')}</p>
      
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">{t('language.select', 'Current Language')}</h3>
        <p className="mb-2">
          {t('common.currentLanguage', 'Current language')}: <strong>{currentLanguage}</strong>
        </p>
        <LanguageSelector />
      </div>
      
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">{t('common.formattedDate', 'Formatted Date')}</h3>
        <p>
          {formatDate(today, { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </p>
      </div>
      
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">{t('common.formattedNumber', 'Formatted Number')}</h3>
        <p>
          {formatNumber(number, { maximumFractionDigits: 2 })}
        </p>
      </div>
      
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">{t('navigation.title', 'Navigation')}</h3>
        <ul className="list-disc pl-5">
          <li>{t('navigation.home')}</li>
          <li>{t('navigation.chat')}</li>
          <li>{t('navigation.profile')}</li>
          <li>{t('navigation.settings')}</li>
          <li>{t('navigation.help')}</li>
          <li>{t('navigation.logout')}</li>
        </ul>
      </div>
      
      <div>
        <h3 className="text-lg font-semibold mb-2">{t('chat.title', 'Chat')}</h3>
        <ul className="list-disc pl-5">
          <li>{t('chat.newChat')}</li>
          <li>{t('chat.placeholder')}</li>
          <li>{t('chat.send')}</li>
          <li>{t('chat.thinking')}</li>
          <li>{t('chat.noMessages')}</li>
        </ul>
      </div>
    </div>
  );
}