import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enUS from './locales/en-US/translation.json';
import enGB from './locales/en-GB/translation.json';

/**
 * Initialize i18next for internationalization
 *
 * Supported languages:
 * - en-US: English (United States) - default
 * - en-GB: English (United Kingdom) - UK spelling variants
 *
 * Language detection order:
 * 1. localStorage key 'i18nextLng'
 * 2. Browser language setting
 * 3. Fallback to en-US
 */
i18n
  .use(LanguageDetector) // Detect user language from browser/localStorage
  .use(initReactI18next) // Pass i18n instance to react-i18next
  .init({
    resources: {
      'en-US': {
        translation: enUS,
      },
      'en-GB': {
        translation: enGB,
      },
    },
    fallbackLng: 'en-US',
    debug: import.meta.env.DEV, // Enable debug logging in development
    interpolation: {
      escapeValue: false, // React already escapes by default
    },
    detection: {
      // Order of language detection methods
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n;
