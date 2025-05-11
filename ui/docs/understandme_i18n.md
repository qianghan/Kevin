# KAI UI Internationalization Documentation

This document provides an overview of the internationalization (i18n) implementation for the KAI UI application, which follows SOLID principles and best practices.

## Overview

The KAI UI application supports multiple languages through a comprehensive internationalization system. The implementation uses:

- **next-i18next**: For integration with Next.js
- **i18next**: Core internationalization library
- **react-i18next**: React bindings for i18next
- **i18next-http-backend**: For loading translations dynamically
- **i18next-browser-languagedetector**: For automatic language detection

## Core Components

### 1. I18nProvider (`components/I18nProvider.tsx`)

The I18nProvider is a higher-order component that wraps the application, providing the i18n context to all components. It initializes i18next with the necessary configuration and provides the translation functionality.

```tsx
<I18nProvider>
  <App />
</I18nProvider>
```

#### Key Features:
- Initializes i18next with standard configuration
- Provides language detection
- Configures backend for loading translation files
- Follows the Single Responsibility Principle (SRP) by focusing solely on i18n functionality

### 2. useI18n Hook (`hooks/useI18n.ts`)

A custom React hook that provides a simplified interface for accessing i18n functionality within components. This custom hook encapsulates the complexities of the i18next API and provides additional utility functions.

```tsx
const { t, currentLanguage, changeLanguage, formatDate, formatNumber } = useI18n();
```

#### Key Features:
- Language switching with URL path updates
- Date formatting according to locale
- Number formatting according to locale
- Access to current language and available languages

### 3. LanguageSelector (`components/LanguageSelector.tsx`)

A reusable component for language selection that adapts to different screen sizes.

```tsx
<LanguageSelector />
```

#### Key Features:
- Provides a dropdown menu for mobile devices
- Shows language buttons for desktop devices
- Highlights the current language
- Handles language switching and navigation updates

## Translation Files

Translation files are stored in the `public/locales` directory, organized by language code:

```
public/locales/
  ├── en/
  │   └── common.json
  ├── fr/
  │   └── common.json
  └── zh/
      └── common.json
```

Each language has a `common.json` file containing translations organized by feature area:

```json
{
  "app": { ... },
  "navigation": { ... },
  "chat": { ... },
  "profile": { ... },
  "settings": { ... },
  "language": { ... },
  "common": { ... }
}
```

## Usage Examples

### Basic Translation

```tsx
import { useI18n } from '@/hooks/useI18n';

export function MyComponent() {
  const { t } = useI18n();
  
  return (
    <div>
      <h1>{t('app.title')}</h1>
      <p>{t('app.description')}</p>
    </div>
  );
}
```

### Date and Number Formatting

```tsx
import { useI18n } from '@/hooks/useI18n';

export function FormattedValues() {
  const { formatDate, formatNumber } = useI18n();
  const today = new Date();
  const amount = 1234567.89;
  
  return (
    <div>
      <p>Date: {formatDate(today)}</p>
      <p>Amount: {formatNumber(amount)}</p>
    </div>
  );
}
```

### Changing Language

```tsx
import { useI18n } from '@/hooks/useI18n';

export function LanguageButton() {
  const { changeLanguage } = useI18n();
  
  return (
    <button onClick={() => changeLanguage('fr')}>
      Switch to French
    </button>
  );
}
```

## Implementation Details

### Dependency Injection (DIP)

The i18n system follows the Dependency Inversion Principle by:
- Defining clear interfaces for i18n services
- Using dependency injection for translation functionality
- Allowing different implementations to be swapped in if needed

### Interface Segregation (ISP)

The interfaces are focused and minimal:
- The translation functions only include what's necessary for each component
- The `useI18n` hook provides a segregated interface focused on specific needs

### Open/Closed Principle (OCP)

The system is designed to be extended without modification:
- New languages can be added without changing the core code
- Additional translation namespaces can be added
- Custom formatters can be integrated without modifying existing code

### Testing

The i18n implementation supports various testing approaches:
- Component testing with mock translations
- Integration testing with the full i18n system
- Testing with different language implementations to ensure compatibility

## Adding a New Language

To add a new language:

1. Create a new directory in `public/locales` with the language code (e.g., `de` for German)
2. Create a `common.json` file with translations
3. Add the language to the `languages` array in `lib/i18n.ts`

## Conclusion

The KAI UI internationalization system provides a solid foundation for multi-language support that is maintainable, extensible, and follows SOLID principles. The system integrates seamlessly with Next.js routing and provides utilities for formatting dates and numbers according to the user's locale. 