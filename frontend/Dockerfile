# Build from this folder:
#   docker build -t frontend .
#   docker run -p 5173:80 frontend
# Backend URLs are baked in at build time (spec §8). They come from the
# corresponding build args if given, otherwise from frontend/.env.
FROM node:24-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL
ARG VITE_API_FALLBACK_URL
# development makes import.meta.env.PROD false, so an http://localhost backend is accepted.
ARG NODE_ENV=production
RUN NODE_ENV=$NODE_ENV npm run build

FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
