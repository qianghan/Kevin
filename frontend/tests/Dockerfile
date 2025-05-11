FROM node:18-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    chromium \
    curl

# Set environment variables
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser \
    NODE_ENV=test

# Install dependencies first (for better caching)
COPY package.json ./
RUN npm install

# Copy test files
COPY . .

# Create directory for test results
RUN mkdir -p test-results

# Command to run tests
CMD ["npm", "run", "test"] 