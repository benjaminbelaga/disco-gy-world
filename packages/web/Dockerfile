# --- build stage ---
FROM node:22-alpine AS build
# Keep the monorepo layout: src/utils/vibeSearch.js imports
# `../../../../docs/electronic-music-taxonomy.json`, which resolves to
# the repo-root docs/ dir — so the web package must sit at packages/web.
WORKDIR /repo/packages/web
COPY packages/web/package*.json ./
# vite-plugin-pwa@1.2.0 peer-deps vite<=7 but project uses vite@8;
# lockfile was resolved with relaxed peers, so match that here.
RUN npm ci --legacy-peer-deps
COPY packages/web ./
COPY docs /repo/docs
RUN npm run build

# --- serve stage ---
FROM nginx:alpine
COPY packages/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /repo/packages/web/dist /usr/share/nginx/html
EXPOSE 80
