# CourseScout web — build the Vite bundle, then serve it with nginx.
#
#   docker build -t coursescout-web ./frontend
#   docker run -p 80:80 coursescout-web
#
# The container talks to the browser on ONE origin: nginx serves the JS/CSS and
# proxies /api, /admin, /static and /media to the Django container (see
# nginx.conf). That means no CORS setup and no absolute URL baked into the JS.

# ---------- Stage 1: build the bundle ----------
FROM node:20-alpine AS build
WORKDIR /app

# Dependencies first → this layer is cached until package.json changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# VITE_API_URL is optional:
#   unset (default) → the bundle calls the same origin (/api) → nginx proxies it
#   http://localhost:8000 → the browser calls Django directly on the host port
ARG VITE_API_URL=
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# ---------- Stage 2: serve with nginx ----------
FROM nginx:1.27-alpine AS serve

# SPA routing + API proxy, one config for both.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
