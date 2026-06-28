ARG NODE_VERSION=24.7.0-alpine

FROM node:${NODE_VERSION} AS dev

WORKDIR /src

COPY ui-9to18/package*.json ./

RUN --mount=type=cache,target=/root/.npm npm install

COPY ui-9to18/ .

EXPOSE 8200

CMD ["npm", "run", "dev"]
