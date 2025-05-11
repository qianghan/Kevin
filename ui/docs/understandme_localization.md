# KAI UI Localization Components Documentation

This document provides detailed information about the localization components implemented in the KAI UI application, which follow SOLID principles and best practices.

## Overview

The KAI UI localization components provide a user-friendly interface for language selection and locale-specific content display. These components are designed to be reusable, accessible, and consistent with the KAI design system.

## Key Components

### 1. LanguageSelector (`components/LanguageSelector.tsx`)

The `LanguageSelector` component provides a user interface for selecting the application language. It adapts to different screen sizes, showing a dropdown on mobile devices and language buttons on desktop.

```tsx
<LanguageSelector />
```

#### Implementation Details:

```tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useI18n } from '@/hooks/useI18n';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

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
```

#### Features:
- Responsive design with different UI for mobile and desktop
- Visual indication of the currently selected language
- Uses Next.js's routing capabilities for language switching
- Follows accessibility best practices

### 2. I18nDemo (`components/I18nDemo.tsx`)

The `I18nDemo` component demonstrates how to use internationalization features in the UI, including text translation, date formatting, and number formatting.

```tsx
<I18nDemo />
```

#### Key Features:
- Examples of text translation using the `t` function
- Date formatting examples based on the current locale
- Number formatting examples based on the current locale
- Language selection interface

### 3. FormattedDate (`components/FormattedDate.tsx`)

A utility component for displaying dates formatted according to the current locale.

```tsx
<FormattedDate date={new Date()} format={{ dateStyle: 'full' }} />
```

#### Implementation:

```tsx
'use client';

import { useI18n } from '@/hooks/useI18n';

interface FormattedDateProps {
  date: Date;
  format?: Intl.DateTimeFormatOptions;
}

export function FormattedDate({ date, format }: FormattedDateProps) {
  const { formatDate } = useI18n();
  return <span>{formatDate(date, format)}</span>;
}
```

### 4. FormattedNumber (`components/FormattedNumber.tsx`)

A utility component for displaying numbers formatted according to the current locale.

```tsx
<FormattedNumber value={1234567.89} format={{ style: 'currency', currency: 'USD' }} />
```

#### Implementation:

```tsx
'use client';

import { useI18n } from '@/hooks/useI18n';

interface FormattedNumberProps {
  value: number;
  format?: Intl.NumberFormatOptions;
}

export function FormattedNumber({ value, format }: FormattedNumberProps) {
  const { formatNumber } = useI18n();
  return <span>{formatNumber(value, format)}</span>;
}
```

## Integration with KAI Design System

The localization components follow the KAI design system guidelines:

1. **Consistent styling**: Components use the same styling patterns as other KAI UI components
2. **Accessibility**: All components meet WCAG 2.1 AA guidelines
3. **Responsive design**: Components adjust their layout based on screen size
4. **Theming support**: Components respect the current theme settings (light/dark mode)

## SOLID Principles in Localization Components

### Single Responsibility Principle (SRP)

Each component has a single responsibility:
- `LanguageSelector` is solely responsible for language selection
- `FormattedDate` is solely responsible for date formatting
- `FormattedNumber` is solely responsible for number formatting

### Open/Closed Principle (OCP)

Components are designed to be extended without modification:
- `LanguageSelector` accepts custom styling props
- Formatting components accept custom format options
- New locale-specific components can be added without changing existing ones

### Liskov Substitution Principle (LSP)

Components can be substituted with alternative implementations that satisfy the same interface:
- Mock implementations can be used for testing
- Alternative date/number formatters can be used if needed

### Interface Segregation Principle (ISP)

Components have minimal, focused interfaces:
- Each component accepts only the props it needs
- The `useI18n` hook provides a focused API for internationalization

### Dependency Inversion Principle (DIP)

Components depend on abstractions rather than concrete implementations:
- Components use the `useI18n` hook which provides an abstraction over the i18n implementation
- Alternative i18n implementations can be provided without changing components

## RTL (Right-to-Left) Support

The localization system includes groundwork for RTL language support:

1. CSS utilities for handling RTL layouts
2. Component design that accommodates text direction changes
3. Documentation for adding RTL languages in the future

## Testing Localization Components

The localization components include tests to verify:

1. Proper rendering with different languages
2. Correct date and number formatting based on locale
3. Language switching functionality
4. Graceful handling of missing translations
5. Proper display of text with different lengths and scripts

## Conclusion

The KAI UI localization components provide a comprehensive solution for internationalization that's both user-friendly and developer-friendly. By following SOLID principles, these components are maintainable, extensible, and integrate seamlessly with the rest of the KAI UI system. 