#!/bin/bash

# API URLs
export NEXT_PUBLIC_API_URL=http://localhost:8000/api
export NEXT_PUBLIC_UI_URL=http://localhost:3001

# Authentication
export NEXT_PUBLIC_AUTH_BYPASS=true
export NEXTAUTH_URL=http://localhost:3001
export NEXTAUTH_SECRET=dev_secret_key_123

# Environment
export NODE_ENV=development

# MongoDB
export MONGODB_URI=mongodb://localhost:27018/kevin
export MONGODB_DB=kevin

# Chat Service
export NEXT_PUBLIC_CHAT_WS_URL=ws://localhost:8000/ws/chat
export NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000/api/chat

echo "Environment variables set successfully!" 