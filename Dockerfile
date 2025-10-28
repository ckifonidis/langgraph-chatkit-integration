# Multi-stage Docker build for LangGraph ChatKit Integration
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

# Build arguments for frontend configuration
ARG VITE_CHATKIT_API_DOMAIN_KEY=domain_pk_68fb64ee20288190943636b0dd461fda010641585abac21c
ARG VITE_CHATKIT_API_URL=/langgraph/chatkit
ARG VITE_GOOGLE_MAPS_API_KEY

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies (including dev dependencies for build)
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend for production with environment variables
RUN VITE_CHATKIT_API_DOMAIN_KEY=$VITE_CHATKIT_API_DOMAIN_KEY \
    VITE_CHATKIT_API_URL=$VITE_CHATKIT_API_URL \
    VITE_GOOGLE_MAPS_API_KEY=$VITE_GOOGLE_MAPS_API_KEY \
    npm run build

# Stage 2: Backend + Nginx
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend files
COPY backend/pyproject.toml ./backend/
COPY backend/app ./backend/app/
COPY backend/chatkit_langgraph ./backend/chatkit_langgraph/
COPY backend/custom_components ./backend/custom_components/
COPY backend/examples ./backend/examples/

# Install backend dependencies using pip
WORKDIR /app/backend
RUN pip install --no-cache-dir -e .

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Configure Nginx
RUN rm /etc/nginx/sites-enabled/default
COPY docker/nginx.conf /etc/nginx/sites-enabled/chatkit

# Configure Supervisor to run both services
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:80/langgraph/health || exit 1

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
