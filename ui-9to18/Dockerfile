# ui-9to18 — standalone SPA for 9to18.ru
# Build context: this directory (.)

ARG NODE_VERSION=24.7.0-alpine
ARG NGINX_VERSION=1.27-alpine

# ---------- build ----------
FROM node:${NODE_VERSION} AS build

WORKDIR /src

COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .
RUN npm run build

# ---------- production (static) ----------
FROM nginx:${NGINX_VERSION} AS production

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/dist /usr/share/nginx/html

EXPOSE 8200

CMD ["nginx", "-g", "daemon off;"]

# ---------- development (Vite) ----------
FROM node:${NODE_VERSION} AS development

WORKDIR /src

COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .
RUN node scripts/copy-pyodide.mjs

EXPOSE 8200

CMD ["npm", "run", "dev"]
