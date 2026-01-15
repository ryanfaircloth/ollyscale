# BSD 3-Clause License
#
# Copyright (c) 2025, Infrastructure Architects, LLC
# All rights reserved.

# Multi-stage build: Node.js build + Alpine nginx runtime

# Stage 1: Build frontend assets
FROM node:20-alpine AS builder

WORKDIR /build

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --prefer-offline --no-audit

# Copy source code
COPY src/ ./src/
COPY vite.config.js tsconfig.json ./

# Build for production
RUN npm run build

# Stage 2: Runtime with nginx
FROM nginx:1.25-alpine

# Install envsubst for runtime config templating
RUN apk add --no-cache gettext

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /build/dist /usr/share/nginx/html

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Expose HTTP port
EXPOSE 8000

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
