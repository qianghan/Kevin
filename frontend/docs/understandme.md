# KAI UI Project

## Setup
1. Clone the repository
2. Run `npm install`
3. Copy `.env.example` to `.env.local` and update values (if needed)
4. Run `npm run dev` to start the development server

## Architecture
This project follows a feature-based architecture with SOLID principles:

- Features are isolated in their own directories
- Services are interface-based with dependency injection
- Components have single responsibilities
- Open-Closed principle is followed through extension points
- Liskov substitution is supported through proper interface implementations

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Shared UI components
│   │   ├── common/     # Basic reusable components
│   │   ├── layout/     # Layout components (Container, Grid, etc.)
│   │   ├── patterns/   # UI patterns (Card, List, etc.)
│   │   ├── forms/      # Form components
│   │   └── feedback/   # User feedback components (alerts, toasts, etc.)
│   ├── features/       # Feature-specific code
│   │   ├── auth/       # Authentication feature
│   │   ├── chat/       # Chat feature
│   │   ├── profile/    # Profile feature
│   │   └── agents/     # Agent marketplace feature
│   ├── hooks/          # Custom React hooks
│   ├── services/       # Service layer
│   ├── models/         # Data models and TypeScript interfaces
│   ├── store/          # State management
│   ├── utils/          # Utility functions
│   ├── theme/          # Chakra UI theming
│   └── pages/          # Next.js pages (if using pages router)
├── app/                # Next.js App router
├── public/             # Static assets
└── docs/               # Project documentation
```

## Feature Structure
Each feature follows a consistent structure:

```
features/auth/
├── components/     # Feature-specific components
├── hooks/          # Feature-specific hooks
├── services/       # Feature-specific services
├── models/         # Feature-specific models
└── pages/          # Feature-specific pages
```

## Development Guidelines

### Components
- Components should follow the Single Responsibility Principle
- Use interface-based props with proper TypeScript typing
- Follow Chakra UI conventions for styling and theming
- All components should be accessible and responsive

### Services
- Services should provide clear interfaces for dependency injection
- Use composition over inheritance
- Service methods should be pure when possible
- Handle errors consistently using the error service

### Testing
- Components should have unit tests for behavior
- Use Jest and React Testing Library
- BDD tests should cover critical user journeys
- Services should have proper unit tests for business logic 