# Kevin.AI Web UI

A Next.js-based web application for the Kevin.AI assistant, providing a modern interface for students and parents to interact with the Kevin.AI.

## Features

- **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS
- **Authentication**: Sign in with Google, Facebook, or email/password
- **User Roles**: Support for student and parent roles with appropriate permissions
- **Enhanced Chat Interface**: Real-time chat with streaming responses, modern gradient styling, and thinking steps visualization
- **Context Summarization**: Intelligent conversation summarization for improved continuity and reduced token usage
- **Session Management**: Create and manage multiple chat sessions
- **Family Management**: Parents can manage students and other parent partners
- **MongoDB Integration**: Persistent storage of users, chat sessions, and messages
- **Service Abstraction Layer**: Clean separation of concerns with frontend and backend service layers
- **Robust Error Handling**: Consistent error handling and logging across all services

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- MongoDB instance (local or cloud)
- Kevin API backend running

### Installation

1. Clone the repository
2. Navigate to the UI directory:
   ```bash
   cd ui
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Copy the example environment file and update with your values:
   ```bash
   cp .env.local.example .env.local
   ```
5. Start the development server:
   ```bash
   npm run dev
   ```

### Environment Variables

- `MONGODB_URI`: MongoDB connection string
- `NEXTAUTH_URL`: Base URL of your application (e.g., http://localhost:3000)
- `NEXTAUTH_SECRET`: Secret key for NextAuth.js
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`: Google OAuth credentials
- `FACEBOOK_CLIENT_ID` and `FACEBOOK_CLIENT_SECRET`: Facebook OAuth credentials
- `NEXT_PUBLIC_KEVIN_API_URL`: URL of the Kevin API backend

## Deployment to Vercel

This application is optimized for deployment on Vercel:

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket)
2. Import the project in the Vercel dashboard
3. Configure the environment variables
4. Deploy

## Project Structure

- `app/`: Next.js App Router pages and API routes
- `components/`: React components
- `lib/`: Utility functions and services
- `models/`: MongoDB schema models
- `public/`: Static assets
- `services/`: Service abstraction layers
  - `api/`: Backend API services
  - `db/`: Database services

## Architecture Overview

The Kevin Chat UI is built with Next.js and follows a modular, component-based architecture with clean separation of concerns:

```
ui/
├── app/                    # Next.js app router
│   └── api/                # API routes
├── features/
│   └── chat/               # Chat feature
│       ├── adapters/       # Adapters connecting context to UI
│       ├── components/     # UI components
│       │   └── default/    # Default implementation of UI components
│       ├── context/        # Context providers
│       └── types/          # TypeScript types
├── lib/
│   ├── services/           # Service layer
│   │   ├── BackendApiService.ts  # Backend communication
│   │   └── db/             # Database services
│   └── types/              # Shared types
└── models/                 # Data models
```

### Component Architecture Diagram

```
┌─────────────────────────┐
│     Next.js Pages       │
└──────────┬──────────────┘
           │ Renders
           ▼
┌──────────────────────────────────────────────────┐
│                 ChatAdapter                       │
│  ┌───────────────┐      ┌────────────────────┐   │
│  │ ChatProvider  │──────│ ChatAdapterInner   │   │
│  └───────────────┘      └────────┬───────────┘   │
└────────────────────────────────┬─┼───────────────┘
                                 │ │ Renders Components
                                 │ │
          ┌────────────────────┬─┘ └─┬────────────────────┬───────────────────┐
          │                    │     │                    │                   │
          ▼                    ▼     ▼                    ▼                   ▼
┌─────────────────┐   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ChatContainer   │   │ ChatHeader      │    │ChatMessageList  │    │ ChatInput       │
└─────────────────┘   └─────────────────┘    └─────────────────┘    └─────────────────┘
          │                    │                    │                        │
          │                    │                    │                        │
          └────────────────────┼────────────────────┼────────────────────────┘
                               │                    │
                               │                    │
                               ▼                    ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                ChatContext                                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  ┌─────────────────────┐  │
│  │ State       │  │ Messages     │  │ API            │  │ Event Streaming     │  │
│  │ Management  │  │ Handling     │  │ Communication  │  │ & Session Management │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  └─────────────────────┘  │
└──────────────────────────────────────────┬───────────────────────────────────────┘
                                           │ API Calls
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               Backend Services                                    │
│     ┌────────────────┐      ┌────────────────┐      ┌────────────────┐           │
│     │/api/chat/query │      │/api/chat/save  │      │/api/chat/sessions│         │
│     └────────────────┘      └────────────────┘      └────────────────┘           │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Core Concepts

### 1. Context-Based State Management

The chat state is managed through React Context (`ChatContext`), which provides:

- Messages state and management
- Loading and thinking states
- Streaming message handling
- Chat session operations (save, update, start new)
- Backend communication via EventSource for streaming responses

### 2. Adapter Pattern

The `ChatAdapter` connects the context to UI components, enabling:

- Loose coupling between business logic and UI
- Easy swapping of UI components
- Reuse of business logic across different UIs

### 3. Component Architecture

UI components are structured with clear responsibilities:

- `ChatContainer`: Layout container
- `ChatHeader`: Title and controls
- `ChatMessageList`: Displays messages and streaming content
- `ChatInput`: User input interface

## Key Components

### ChatContext

The heart of the application, `ChatContext` manages:

- Chat messages array
- Loading and thinking states
- Stream handling via EventSource
- Backend API communication
- Session saving and loading

```typescript
interface ChatContextType {
  messages: ChatMessage[];
  isLoading: boolean;
  streamingMessage: string;
  thinkingSteps: ThinkingStep[];
  isThinking: boolean;
  sendMessage: (message: string) => void;
  startNewChat: () => void;
  clearChat: () => void;
  updateTitle: (title: string) => Promise<boolean>;
  saveChatSession: (title?: string) => Promise<boolean>;
  conversationId?: string;
  useWebSearch: boolean;
  toggleWebSearch: () => void;
  // ...other properties
}
```

### ChatAdapter

Connects the context to UI components:

```typescript
function ChatAdapter({
  components,
  initialConversationId,
  initialMessages = []
}: ChatAdapterProps) {
  return (
    <ChatProvider>
      <ChatAdapterInner components={components} />
    </ChatProvider>
  );
}
```

## Customization Guide

### Creating Custom UI Components

To create a custom UI, implement the interfaces defined in `ui/features/chat/types/chat-ui.types.ts`:

1. `ChatContainerProps`
2. `ChatHeaderProps`
3. `ChatMessageListProps`
4. `ChatInputProps`

For example, to create a custom chat input:

```typescript
import { ChatInputProps } from '../types/chat-ui.types';

export function CustomChatInput({
  onSendMessage,
  isDisabled,
  placeholder,
  useWebSearch,
  onToggleWebSearch
}: ChatInputProps) {
  // Your custom implementation
}
```

### Using the Adapter

Once you have your custom components, use the adapter to connect them:

```typescript
import { ChatAdapter } from '@/features/chat/adapters/ChatAdapter';
import CustomChatContainer from './CustomChatContainer';
import CustomChatHeader from './CustomChatHeader';
import CustomChatMessageList from './CustomChatMessageList';
import CustomChatInput from './CustomChatInput';

export function CustomChat() {
  return (
    <ChatAdapter
      components={{
        ChatContainer: CustomChatContainer,
        ChatHeader: CustomChatHeader,
        ChatMessageList: CustomChatMessageList,
        ChatInput: CustomChatInput
      }}
    />
  );
}
```

### Direct Context Usage

For advanced use cases, you can use the context directly:

```typescript
import { useChatContext } from '@/features/chat/context/ChatContext';

function MyCustomComponent() {
  const { messages, sendMessage, isLoading } = useChatContext();
  // Your custom implementation
}
```

## Backend Integration

The UI communicates with the backend through:

1. **REST API Endpoints**:
   - `/api/chat/query`: Send chat messages
   - `/api/chat/save`: Save chat sessions
   - `/api/chat/sessions/`: Manage sessions

2. **Event Streaming**:
   - Uses EventSource for real-time response streaming
   - Handles different event types (thinking, chunks, done)

To integrate with a different backend:

1. Update the `BackendApiService` configuration
2. Ensure the backend supports the expected event format for streaming
3. Implement the required API endpoints or adapt the UI to your backend's API

## Advanced Features

### Web Search Integration

The chat UI supports toggling web search functionality:

```typescript
// In ChatInput
<button onClick={onToggleWebSearch}>
  {useWebSearch ? 'Disable Web Search' : 'Enable Web Search'}
</button>
```

The `useWebSearch` flag is passed to the backend API.

### Chat Session Persistence

Chat sessions are automatically saved:
- After message exchanges
- Before starting a new chat
- When navigating away

The title is derived from the first user message or can be manually set.

## Default Components

Default implementations are provided in `ui/features/chat/components/default/`:

- `DefaultChatContainer.tsx`: Basic layout container
- `DefaultChatHeader.tsx`: Header with title editing and controls
- `DefaultChatMessageList.tsx`: Message rendering with Markdown support
- `DefaultChatInput.tsx`: Input field with web search toggle

These components can be used as-is, extended, or replaced with custom ones.

## Getting Started

1. Import the necessary components
2. Set up the adapter with your components (or use the defaults)
3. Render the adapter in your application

```typescript
import { ChatAdapter } from '@/features/chat/adapters/ChatAdapter';
import { DefaultChatContainer, DefaultChatHeader, DefaultChatMessageList, DefaultChatInput } 
  from '@/features/chat/components/default';

export default function ChatPage() {
  return (
    <ChatAdapter
      components={{
        ChatContainer: DefaultChatContainer,
        ChatHeader: DefaultChatHeader,
        ChatMessageList: DefaultChatMessageList,
        ChatInput: DefaultChatInput
      }}
    />
  );
}
```

## Summary

The Kevin Chat UI provides a flexible, component-based architecture that:
- Separates state management from UI rendering
- Allows easy customization of UI components
- Handles complex streaming interactions
- Provides session persistence
- Supports advanced features like web search

This design makes it easy to adapt the UI to different requirements while reusing the core business logic.

## License

[MIT](LICENSE)

# Kevin Chat UI Architecture

This document explains the architecture of the Kevin Chat UI, how the components work together, and how to customize or port the UI to your own application.

## Architecture Overview

The Kevin Chat UI is built with Next.js and follows a modular, component-based architecture with clean separation of concerns:

```
ui/
├── app/                    # Next.js app router
│   └── api/                # API routes
├── features/
│   └── chat/               # Chat feature
│       ├── adapters/       # Adapters connecting context to UI
│       ├── components/     # UI components
│       │   └── default/    # Default implementation of UI components
│       ├── context/        # Context providers
│       └── types/          # TypeScript types
├── lib/
│   ├── services/           # Service layer
│   │   ├── BackendApiService.ts  # Backend communication
│   │   └── db/             # Database services
│   └── types/              # Shared types
└── models/                 # Data models
```

### Component Architecture Diagram

```
┌─────────────────────────┐
│     Next.js Pages       │
└──────────┬──────────────┘
           │ Renders
           ▼
┌──────────────────────────────────────────────────┐
│                 ChatAdapter                       │
│  ┌───────────────┐      ┌────────────────────┐   │
│  │ ChatProvider  │──────│ ChatAdapterInner   │   │
│  └───────────────┘      └────────┬───────────┘   │
└────────────────────────────────┬─┼───────────────┘
                                 │ │ Renders Components
                                 │ │
          ┌────────────────────┬─┘ └─┬────────────────────┬───────────────────┐
          │                    │     │                    │                   │
          ▼                    ▼     ▼                    ▼                   ▼
┌─────────────────┐   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ChatContainer   │   │ ChatHeader      │    │ChatMessageList  │    │ ChatInput       │
└─────────────────┘   └─────────────────┘    └─────────────────┘    └─────────────────┘
          │                    │                    │                        │
          │                    │                    │                        │
          └────────────────────┼────────────────────┼────────────────────────┘
                               │                    │
                               │                    │
                               ▼                    ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                ChatContext                                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  ┌─────────────────────┐  │
│  │ State       │  │ Messages     │  │ API            │  │ Event Streaming     │  │
│  │ Management  │  │ Handling     │  │ Communication  │  │ & Session Management │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  └─────────────────────┘  │
└──────────────────────────────────────────┬───────────────────────────────────────┘
                                           │ API Calls
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               Backend Services                                    │
│     ┌────────────────┐      ┌────────────────┐      ┌────────────────┐           │
│     │/api/chat/query │      │/api/chat/save  │      │/api/chat/sessions│         │
│     └────────────────┘      └────────────────┘      └────────────────┘           │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Core Concepts

### 1. Context-Based State Management

The chat state is managed through React Context (`ChatContext`), which provides:

- Messages state and management
- Loading and thinking states
- Streaming message handling
- Chat session operations (save, update, start new)
- Backend communication via EventSource for streaming responses

### 2. Adapter Pattern

The `ChatAdapter` connects the context to UI components, enabling:

- Loose coupling between business logic and UI
- Easy swapping of UI components
- Reuse of business logic across different UIs

### 3. Component Architecture

UI components are structured with clear responsibilities:

- `ChatContainer`: Layout container
- `ChatHeader`: Title and controls
- `ChatMessageList`: Displays messages and streaming content
- `ChatInput`: User input interface

## Key Components

### ChatContext

The heart of the application, `ChatContext` manages:

- Chat messages array
- Loading and thinking states
- Stream handling via EventSource
- Backend API communication
- Session saving and loading

```typescript
interface ChatContextType {
  messages: ChatMessage[];
  isLoading: boolean;
  streamingMessage: string;
  thinkingSteps: ThinkingStep[];
  isThinking: boolean;
  sendMessage: (message: string) => void;
  startNewChat: () => void;
  clearChat: () => void;
  updateTitle: (title: string) => Promise<boolean>;
  saveChatSession: (title?: string) => Promise<boolean>;
  conversationId?: string;
  useWebSearch: boolean;
  toggleWebSearch: () => void;
  // ...other properties
}
```

### ChatAdapter

Connects the context to UI components:

```typescript
function ChatAdapter({
  components,
  initialConversationId,
  initialMessages = []
}: ChatAdapterProps) {
  return (
    <ChatProvider>
      <ChatAdapterInner components={components} />
    </ChatProvider>
  );
}
```

## Customization Guide

### Creating Custom UI Components

To create a custom UI, implement the interfaces defined in `ui/features/chat/types/chat-ui.types.ts`:

1. `ChatContainerProps`
2. `ChatHeaderProps`
3. `ChatMessageListProps`
4. `ChatInputProps`

For example, to create a custom chat input:

```typescript
import { ChatInputProps } from '../types/chat-ui.types';

export function CustomChatInput({
  onSendMessage,
  isDisabled,
  placeholder,
  useWebSearch,
  onToggleWebSearch
}: ChatInputProps) {
  // Your custom implementation
}
```

### Using the Adapter

Once you have your custom components, use the adapter to connect them:

```typescript
import { ChatAdapter } from '@/features/chat/adapters/ChatAdapter';
import CustomChatContainer from './CustomChatContainer';
import CustomChatHeader from './CustomChatHeader';
import CustomChatMessageList from './CustomChatMessageList';
import CustomChatInput from './CustomChatInput';

export function CustomChat() {
  return (
    <ChatAdapter
      components={{
        ChatContainer: CustomChatContainer,
        ChatHeader: CustomChatHeader,
        ChatMessageList: CustomChatMessageList,
        ChatInput: CustomChatInput
      }}
    />
  );
}
```

### Direct Context Usage

For advanced use cases, you can use the context directly:

```typescript
import { useChatContext } from '@/features/chat/context/ChatContext';

function MyCustomComponent() {
  const { messages, sendMessage, isLoading } = useChatContext();
  // Your custom implementation
}
```

## Backend Integration

The UI communicates with the backend through:

1. **REST API Endpoints**:
   - `/api/chat/query`: Send chat messages
   - `/api/chat/save`: Save chat sessions
   - `/api/chat/sessions/`: Manage sessions

2. **Event Streaming**:
   - Uses EventSource for real-time response streaming
   - Handles different event types (thinking, chunks, done)

To integrate with a different backend:

1. Update the `BackendApiService` configuration
2. Ensure the backend supports the expected event format for streaming
3. Implement the required API endpoints or adapt the UI to your backend's API

## Advanced Features

### Web Search Integration

The chat UI supports toggling web search functionality:

```typescript
// In ChatInput
<button onClick={onToggleWebSearch}>
  {useWebSearch ? 'Disable Web Search' : 'Enable Web Search'}
</button>
```

The `useWebSearch` flag is passed to the backend API.

### Chat Session Persistence

Chat sessions are automatically saved:
- After message exchanges
- Before starting a new chat
- When navigating away

The title is derived from the first user message or can be manually set.

## Default Components

Default implementations are provided in `ui/features/chat/components/default/`:

- `DefaultChatContainer.tsx`: Basic layout container
- `DefaultChatHeader.tsx`: Header with title editing and controls
- `DefaultChatMessageList.tsx`: Message rendering with Markdown support
- `DefaultChatInput.tsx`: Input field with web search toggle

These components can be used as-is, extended, or replaced with custom ones.

## Getting Started

1. Import the necessary components
2. Set up the adapter with your components (or use the defaults)
3. Render the adapter in your application

```typescript
import { ChatAdapter } from '@/features/chat/adapters/ChatAdapter';
import { DefaultChatContainer, DefaultChatHeader, DefaultChatMessageList, DefaultChatInput } 
  from '@/features/chat/components/default';

export default function ChatPage() {
  return (
    <ChatAdapter
      components={{
        ChatContainer: DefaultChatContainer,
        ChatHeader: DefaultChatHeader,
        ChatMessageList: DefaultChatMessageList,
        ChatInput: DefaultChatInput
      }}
    />
  );
}
```

## Deploying to Vercel

The Kevin Chat UI is optimized for deployment on Vercel. Follow these steps to deploy your application:

### 1. Configure Environment Variables

Set up the following environment variables in your Vercel project:

- `MONGODB_URI`: Connection string for MongoDB (MongoDB Atlas recommended for Vercel)
- `NEXTAUTH_URL`: The canonical URL of your site (e.g., https://your-app.vercel.app)
- `NEXTAUTH_SECRET`: Secret for NextAuth.js (generate with `openssl rand -base64 32`)
- `NEXT_PUBLIC_KEVIN_API_URL`: URL to your backend API (if separate from this UI)

See `.env.example` for a complete list of environment variables.

### 2. Database Configuration

For best performance on Vercel:

- Use MongoDB Atlas for your database
- Configure proper connection pooling (already set in the code)
- Ensure your database is in the same region as your Vercel deployment

### 3. Deploy on Vercel

Deploy the application using one of these methods:

**Using Vercel CLI:**

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel
```

**Using GitHub Integration:**

1. Push your code to GitHub
2. Import the repository in the Vercel dashboard
3. Configure your project settings
4. Deploy

### 4. Vercel-Specific Optimizations

The codebase includes several optimizations for Vercel:

- `vercel.json`: Configuration for Vercel deployment
- Database connection pooling suitable for serverless environments
- Timeout handling for API routes
- Proper caching headers for better performance
- Standalone output mode in Next.js config

### 5. Monitoring and Logs

Monitor your application's performance using:

- Vercel Analytics dashboard
- MongoDB Atlas monitoring tools
- Custom logs implemented in the application

### 6. Scaling Considerations

For high traffic applications:

- Consider using Vercel Enterprise for dedicated instances
- Implement a caching layer with Redis (requires additional setup)
- Use MongoDB Atlas with proper scaling configuration
- Consider using Edge Functions for low-latency responses

## Summary

The Kevin Chat UI provides a flexible, component-based architecture that:
- Separates state management from UI rendering
- Allows easy customization of UI components
- Handles complex streaming interactions
- Provides session persistence
- Supports advanced features like web search

This design makes it easy to adapt the UI to different requirements while reusing the core business logic.
