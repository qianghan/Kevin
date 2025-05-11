# KAI UI Translation Management Documentation

This document provides information about the translation management system implemented for the KAI UI application.

## Overview

The KAI UI translation system manages translations for multiple languages using a structured JSON-based approach. The system supports:

- English (en)
- Chinese Simplified (zh)
- French (fr)

## Translation File Structure

Translations are stored in JSON files organized by language and namespace:

```
public/locales/
  ├── en/             # English translations
  │   └── common.json
  ├── zh/             # Chinese Simplified translations
  │   └── common.json
  └── fr/             # French translations
      └── common.json
```

Each language follows the same structure, with the `common.json` file containing all translations for the core application.

## Translation JSON Structure

Translations are organized in a hierarchical structure by feature area:

```json
{
  "app": {
    "title": "KAI",
    "description": "Your AI-powered academic assistant"
  },
  "navigation": {
    "home": "Home",
    "chat": "Chat",
    "profile": "Profile",
    "settings": "Settings",
    "help": "Help",
    "logout": "Logout"
  },
  "chat": {
    "newChat": "New Chat",
    "placeholder": "Ask me anything...",
    "send": "Send",
    "thinking": "Thinking...",
    "noMessages": "No messages yet. Start a conversation!",
    "savedChats": "Saved Chats",
    "loadMore": "Load More",
    "exportChat": "Export Chat",
    "deleteChat": "Delete Chat",
    "search": "Search in chats"
  },
  ...
}
```

This structure helps:
- Organize translations by feature
- Maintain consistency across languages
- Simplify the addition of new translations

## Key Naming Conventions

Translation keys follow these conventions:

1. Use camelCase for keys
2. Start with the feature area (e.g., `app`, `navigation`, `chat`)
3. Use dot notation for access (e.g., `t('navigation.home')`)
4. Keep keys consistent across different language files

## Translation Management Process

The process for managing translations follows these steps:

1. **Development**: Add new keys to the English (`en/common.json`) file first
2. **Translation**: Translate the keys to other supported languages
3. **Review**: Have native speakers review the translations for accuracy
4. **Integration**: Update all language files with the new translations
5. **Testing**: Test the application with each supported language

## Adding a New Language

To add a new language:

1. Create a new directory in `public/locales` with the language code (e.g., `de` for German)
2. Copy the structure of `en/common.json` to maintain consistency
3. Translate all strings in the JSON file
4. Add the language to the `languages` array in `lib/i18n.ts`:

```typescript
export const languages = [
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文 (简体)' },
  { code: 'fr', name: 'Français' },
  { code: 'de', name: 'Deutsch' } // New language
];
```

## Handling Missing Translations

The system handles missing translations by:

1. Falling back to the English version if a key is missing in the current language
2. Displaying the key itself as a last resort
3. Logging missing translations in development mode for easier debugging

## Locale-Specific Formatting

The system provides locale-specific formatting for:

### Dates

```typescript
// Format a date according to the current locale
const { formatDate } = useI18n();
const formattedDate = formatDate(new Date(), {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric'
});
```

### Numbers

```typescript
// Format a number according to the current locale
const { formatNumber } = useI18n();
const formattedNumber = formatNumber(1234567.89, {
  style: 'currency',
  currency: 'USD'
});
```

## Translation Keys Reference

Below is a reference of the main translation key categories:

### App Information
- `app.title`: Application title
- `app.description`: Brief description of the application

### Navigation
- `navigation.home`: Home page link
- `navigation.chat`: Chat page link
- `navigation.profile`: Profile page link
- `navigation.settings`: Settings page link
- `navigation.help`: Help page link
- `navigation.logout`: Logout link

### Chat
- `chat.newChat`: New chat button
- `chat.placeholder`: Input placeholder
- `chat.send`: Send button
- `chat.thinking`: Thinking indicator
- `chat.noMessages`: Empty state message
- `chat.savedChats`: Saved chats label
- `chat.loadMore`: Load more button
- `chat.exportChat`: Export button
- `chat.deleteChat`: Delete button
- `chat.search`: Search placeholder

### Profile
- `profile.name`: Name field
- `profile.email`: Email field
- `profile.language`: Language field
- `profile.darkMode`: Dark mode toggle
- `profile.save`: Save button
- `profile.changePassword`: Change password button
- `profile.currentPassword`: Current password field
- `profile.newPassword`: New password field
- `profile.confirmPassword`: Confirm password field

### Settings
- `settings.general`: General settings tab
- `settings.account`: Account settings tab
- `settings.notifications`: Notifications settings tab
- `settings.privacy`: Privacy settings tab
- `settings.language`: Language settings tab
- `settings.theme`: Theme settings tab
- `settings.autoSave`: Auto-save toggle

### Common UI Elements
- `common.save`: Save button
- `common.cancel`: Cancel button
- `common.delete`: Delete button
- `common.edit`: Edit button
- `common.search`: Search label
- `common.loading`: Loading indicator
- `common.error`: Error message
- `common.success`: Success message
- `common.confirm`: Confirm button
- `common.back`: Back button

## Best Practices

1. **Consistency**: Use consistent terminology across the application
2. **Context**: Provide context for translators about where strings are used
3. **Variables**: Use placeholders for dynamic content (e.g., `{userName}`)
4. **Length**: Be aware of text length differences between languages
5. **Pluralization**: Use i18next's pluralization feature for quantity-dependent text
6. **Formatting**: Use locale-specific formatting for dates, numbers, and currencies
7. **Testing**: Test with long strings, short strings, and different character sets

## Conclusion

The KAI UI translation management system provides a robust foundation for multilingual support. By following consistent patterns and best practices, the system ensures a seamless experience for users across different languages and locales. 