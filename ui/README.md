# Kevin Web UI

A Next.js-based web application for the Kevin AI assistant, providing a modern interface for students and parents to interact with the Kevin AI.

## Features

- **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS
- **Authentication**: Sign in with Google, Facebook, or email/password
- **User Roles**: Support for student and parent roles with appropriate permissions
- **Chat Interface**: Real-time chat with streaming responses and thinking steps visualization
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

## Authentication Flow

1. Users sign in with Google, Facebook, or email/password
2. New users are directed to the registration page to select their role (student or parent)
3. Parents can add students and other parent partners to their family
4. Authentication state is managed with NextAuth.js and JWT tokens

## Chat System

- Real-time chat with streaming responses using Server-Sent Events (SSE)
- Visualization of AI thinking steps
- Support for multiple chat sessions per user
- Persistent storage of chat history in MongoDB

## License

[MIT](LICENSE)
