# syntax=docker/dockerfile:1
FROM node:20-alpine AS base
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci --production

# Copy source
COPY . .

# Build the app
RUN npm run build

# Expose runtime port
EXPOSE 3000

# Run the application
CMD ["npm", "start"]
