FROM node:20-alpine AS base
WORKDIR /app
COPY package.json package-lock.json* ./

# Development stage
FROM base AS dev
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Build stage
FROM base AS builder
RUN npm install
COPY . .
RUN npx vite build

# Production stage
FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
# Store as template; envsubst will substitute $PORT and $BACKEND_URL at runtime
COPY nginx.conf /etc/nginx/templates/default.conf.template
EXPOSE 80
# envsubst only replaces PORT and BACKEND_URL — nginx vars like $http_host are left intact
CMD ["/bin/sh", "-c", "envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
