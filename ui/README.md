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

### Service Abstraction Layers

The application implements a multi-layered service architecture that separates concerns and improves maintainability:

#### 1. Frontend Service Layer (`ChatService`)
- Provides a clean API for UI components to interact with the backend
- Handles error management and retry logic
- Implements consistent logging across all operations
- Abstracts away API implementation details from the UI

#### 2. Backend Service Layer
- **API Services** (`BackendApiService`, `ApiChatService`)
  - Manages HTTP communication with backend APIs
  - Implements robust error handling and request retries
  - Provides structured logging of requests and responses
  - Standardizes API responses for frontend consumption

- **Database Services** (`ChatSessionService`)
  - Encapsulates database operations and queries
  - Handles connection management
  - Implements data validation and error handling
  - Provides consistent logging for database operations

### Detailed Service Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                 UI Layer                                   │
│                                                                           │
│  ┌─────────────┐  ┌────────────────┐  ┌────────────────┐  ┌─────────────┐ │
│  │ Chat Page   │  │ Sessions Page  │  │ Dashboard Page │  │ Other Pages │ │
│  └──────┬──────┘  └────────┬───────┘  └────────┬───────┘  └─────┬───────┘ │
└─────────┼───────────────────┼────────────────────┼──────────────┼─────────┘
          │                   │                    │              │
          │                   │                    │              │
          ▼                   ▼                    ▼              ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         Frontend Service Layer                             │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                          ChatService                                 │  │
│  │                                                                      │  │
│  │  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────────┐   │  │
│  │  │saveConversation│ │getConversation│  │...other service methods │   │  │
│  │  └──────────────┘  └───────────────┘  └─────────────────────────┘   │  │
│  └────────────────────────────────────┬──────────────────────────────────┘  │
└────────────────────────────────────────┼──────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         Backend Service Layer                              │
│                                                                           │
│  ┌─────────────────────┐          ┌───────────────────────────────────┐   │
│  │   API Services      │          │      Database Services            │   │
│  │                     │          │                                   │   │
│  │  ┌───────────────┐  │          │  ┌─────────────────────────────┐ │   │
│  │  │BackendApiService│──┐        │  │      ChatSessionService     │ │   │
│  │  └───────────────┘  │ │        │  │                             │ │   │
│  │         ▲           │ │        │  │ ┌─────────────┐ ┌─────────┐ │ │   │
│  │         │           │ │        │  │ │saveSession  │ │getConv...│ │ │   │
│  │  ┌───────────────┐  │ │        │  │ └─────────────┘ └─────────┘ │ │   │
│  │  │ ApiChatService │◀─┘ │        │  └──────────────┬──────────────┘ │   │
│  │  └───────────────┘    │        │                 │                │   │
│  └─────────┬─────────────┘        └─────────────────┼────────────────┘   │
└────────────┼──────────────────────────────────────┬─┼────────────────────┘
             │                                      │ │
             ▼                                      │ │
┌────────────────────────┐                          │ │
│                        │                          │ │
│    Next.js API Routes  │◀─────────────────────────┘ │
│                        │                            │
└───────────┬────────────┘                            │
            │                                         │
            ▼                                         │
┌────────────────────────┐                            │
│                        │                            │
│   Kevin.AI FastAPI     │                            │
│                        │                            │
└───────────┬────────────┘                            │
            │                                         │
            ▼                                         ▼
┌────────────────────────┐            ┌────────────────────────┐
│                        │            │                        │
│   External Services    │            │      MongoDB           │
│   (DeepSeek, Tavily)   │            │                        │
│                        │            │                        │
└────────────────────────┘            └────────────────────────┘
```

### Data Flow

1. **UI Layer to Frontend Service**:
   - UI components call methods from the `ChatService`
   - Frontend service handles error display, loading states, and data formatting

2. **Frontend Service to Backend Services**:
   - `ChatService` delegates to appropriate backend services
   - API services handle HTTP communication
   - Database services handle direct database operations

3. **Backend Services to External Systems**:
   - API services communicate with Next.js API routes or external APIs
   - Database services interact directly with MongoDB

4. **Response Flow**:
   - Data returns through the same layers with appropriate transformations
   - Errors are handled at each layer with proper logging and user-friendly messages

### Service Responsibilities

#### Frontend Service (`ChatService`)
- **User Interaction**: Provides methods for all chat-related operations
- **Error Handling**: Gracefully handles errors for improved user experience
- **Retry Logic**: Implements automatic retries for network-related failures
- **Data Formatting**: Ensures consistent data structures for UI components

#### API Services
- **`BackendApiService`**:
  - General-purpose HTTP client with robust error handling
  - Implements retry mechanisms for transient failures
  - Provides detailed logging of requests and responses
  - Standardizes error responses

- **`ApiChatService`**:
  - Chat-specific API operations using `BackendApiService`
  - Handles data transformation for API endpoints
  - Implements specific error handling for chat operations

#### Database Services (`ChatSessionService`)
- **Data Access**: Encapsulates all MongoDB operations
- **Validation**: Validates data before persistence
- **Error Management**: Handles database-specific errors
- **Performance Logging**: Tracks query performance

### Authentication Flow

1. Users sign in with Google, Facebook, or email/password
2. New users are directed to the registration page to select their role (student or parent)
3. Parents can add students and other parent partners to their family
4. Authentication state is managed with NextAuth.js and JWT tokens

## Chat System

- Real-time chat with streaming responses using Server-Sent Events (SSE)
- Visualization of AI thinking steps
- Modern UI with gradient backgrounds and improved contrast
- Support for multiple chat sessions per user
- Persistent storage of chat history in MongoDB
- Context summarization for improved conversation continuity and reduced token usage

### Context Summarization

The chat system now includes intelligent context summarization capabilities:

- **Optimized Token Usage**: Generates concise summaries of conversation history to reduce the tokens sent to the AI model
- **Improved Continuity**: Helps the AI maintain context across longer conversations without requiring the full message history
- **Smart Summarization Logic**:
  - For short conversations (≤3 messages): Simple formatting of the complete context
  - For longer conversations: Sophisticated summarization that extracts key questions and recent exchanges
- **Database Integration**: Context summaries are stored alongside chat sessions in MongoDB

### UI Enhancements

Recent UI improvements include:

- **Modern Aesthetic**: Gradient backgrounds and improved color schemes for better visual appeal
- **Improved Message Styling**:
  - User messages: Gradient background with white text for better readability
  - Assistant messages: Clean white background with dark text
- **Enhanced Interaction**: Hover effects, copy buttons, and better spacing for improved usability
- **Responsive Design**: Adaptable layout that works well on mobile and desktop devices
- **Visual Hierarchy**: Better distinction between user and assistant messages for easier conversation reading

### Logging and Error Handling

The application implements comprehensive logging and error handling:

- **Structured Logging**: Consistent format with contextual information
- **Error Classification**: Categorized errors for better debugging
- **Request Tracing**: Request IDs for tracking issues across services
- **Performance Metrics**: Timing information for operations
- **Client-Side Feedback**: User-friendly error messages
- **Retry Mechanisms**: Automatic retries for transient failures

## License

[MIT](LICENSE)
