# Frontend Dockerfile for development and production

FROM node:20-alpine AS base
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --silent

# Copy rest
COPY . ./

# Development image
FROM base AS development
ENV NODE_ENV=development
CMD ["npm", "run", "dev"]

# Production build
FROM base AS build
ENV NODE_ENV=production
RUN npm run build

# Serve using a lightweight server
FROM nginx:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
