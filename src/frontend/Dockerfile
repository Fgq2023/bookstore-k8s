# src/frontend/Dockerfile
# Multi-stage build: Node build → nginx serve

# ─── Stage 1: Build ───
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ─── Stage 2: Runtime ───
FROM nginx:1.25-alpine

# Patch base image vulnerabilities
RUN apk upgrade --no-cache

# Remove default config
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy custom config + built static files
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

# Pre-create and chown nginx paths for non-root (UID 101)
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/cache/nginx /var/log/nginx /var/run/nginx.pid \
    && chmod -R 755 /var/cache/nginx /var/log/nginx /var/run/nginx.pid

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
