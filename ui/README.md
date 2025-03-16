# Kevin Web UI

A Next.js-based web application for the Kevin AI assistant, providing a modern interface for students and parents to interact with the Kevin AI.

## Features

- **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS
- **Authentication**: Sign in with Google, Facebook, or email/password
- **User Roles**: Support for student and parent roles with appropriate permissions
- **Enhanced Chat Interface**: Real-time chat with streaming responses, modern gradient styling, and thinking steps visualization
- **Context Summarization**: Intelligent conversation summarization for improved continuity and reduced token usage
- **Session Management**: Create and manage multiple chat sessions
- **Family Management**: Parents can manage students and other parent partners
- **MongoDB Integration**: Persistent storage of users, chat sessions, and messages

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

## UI Architecture

```
┌───────────────────────────────────────────────────────┐
│                  Next.js Application                  │
└───────────────────────────────────────────────────────┘
                            │
┌──────────────┬────────────┴───────────┬───────────────┐
│              │                        │               │
▼              ▼                        ▼               ▼
┌──────────┐ ┌────────────────┐  ┌─────────────┐  ┌────────────┐
│  App     │ │  Components    │  │   Lib       │  │  Models    │
│  Router  │ │                │  │             │  │            │
└──────────┘ └────────────────┘  └─────────────┘  └────────────┘
     │               │                  │                │
     ▼               ▼                  ▼                ▼
┌──────────┐ ┌────────────────┐  ┌─────────────┐  ┌────────────┐
│ Pages    │ │ Auth           │  │ API Client  │  │ User       │
│          │ │ Chat           │  │ Auth Utils  │  │ ChatSession│
│ - Home   │ │ Dashboard      │  │ DB Utils    │  │            │
│ - Auth   │ │ UI Components  │  │ Utilities   │  │            │
│ - Dash   │ │ Forms          │  │             │  │            │
└──────────┘ └────────────────┘  └─────────────┘  └────────────┘
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │  Kevin FastAPI      │
                              │  Backend            │
                              └─────────────────────┘
```

### Detailed Architecture Explanation

#### 1. App Router Structure (App Directory)
- **Modern Next.js 13+ App Router** - Uses the new file-based routing system
- **Route Groups**:
  - `(auth)`: Contains authentication-related pages like login, signup
  - `(dashboard)`: Contains protected pages that require authentication
  - `api`: API routes for server-side operations, including NextAuth endpoints

#### 2. Component Architecture (Components Directory)
- **Component Categories**:
  - `auth/`: Authentication components including SessionProvider
  - `chat/`: Chat interface components for interacting with Kevin AI
  - `dashboard/`: Admin and user dashboard components
  - `forms/`: Reusable form components
  - `ui/`: Reusable UI elements (buttons, cards, modals, etc.)

#### 3. Library Layer (Lib Directory)
- **Service Categories**:
  - `api/`: API client for communicating with the Kevin FastAPI backend
  - `auth/`: Authentication utilities and NextAuth configuration
  - `db/`: Database connection and utilities for MongoDB
  - `utils/`: General utility functions and context summarization

#### 4. Data Models (Models Directory)
- **MongoDB Schemas**:
  - `User.ts`: User model with role-based permissions
  - `ChatSession.ts`: Chat session model for storing conversations and context summaries

#### 5. Authentication Flow
```
┌─────────┐     ┌─────────────┐     ┌───────────┐     ┌────────────┐
│  Login  │────▶│  NextAuth   │────▶│  JWT      │────▶│ Protected  │
│  Page   │     │  Provider   │     │  Session  │     │ Routes     │
└─────────┘     └─────────────┘     └───────────┘     └────────────┘
      │                │
      │                ▼
┌─────▼──────┐  ┌─────────────┐
│  OAuth     │  │  MongoDB    │
│  Providers │  │  User Data  │
└────────────┘  └─────────────┘
```

#### 6. Chat Interface Flow
```
┌─────────────┐    ┌────────────┐    ┌────────────┐    ┌───────────┐
│ Chat        │───▶│ API Client │───▶│ Kevin      │───▶│ Stream    │
│ Interface   │    │            │    │ Backend    │    │ Response  │
└─────────────┘    └────────────┘    └────────────┘    └───────────┘
       │                │                                    │
       │                │                                    │
       │                ▼                                    │
       │         ┌────────────┐                             │
       │         │ Context    │                             │
       │         │ Summary    │                             │
       │         └────────────┘                             │
       │                │                                   │
       ▼                ▼                                   ▼
┌─────────────┐  ┌────────────┐               ┌───────────────┐
│ Chat        │◀─┤ Database   │◀──────────────│ Update UI     │
│ History     │  │ Storage    │               │ with Response │
└─────────────┘  └────────────┘               └───────────────┘
```

#### 7. State Management
- **Client-side State**: React hooks and context API
- **Server-side State**: MongoDB for persistence
- **Session State**: NextAuth.js SessionProvider

## Authentication Flow

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

## License

[MIT](LICENSE)
