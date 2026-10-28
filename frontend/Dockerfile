# Build from this folder:
#   docker build -t frontend .
#   docker run -p 5173:80 frontend
# The backend URL is baked in at build time (spec §8). It comes from the
# VITE_API_BASE_URL build arg if given (Render passes service env vars as build
# args), otherwise from frontend/.env.
FROM node:24-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
