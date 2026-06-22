# ui-app/Dockerfile
# =========================================
# Stage 1: Develop the React.js Application
# =========================================
ARG NODE_VERSION=24.7.0-alpine

# Use a lightweight Node.js image for development
FROM node:${NODE_VERSION} AS dev

# Set the working directory inside the container
WORKDIR /src

# Copy package-related files first to leverage Docker's caching mechanism.
# Build context is repo root (see docker-compose), so paths must include ui-app/.
COPY ui-app/package*.json ./

# Install project dependencies
RUN --mount=type=cache,target=/root/.npm npm install

# Copy the rest of the application source code into the container
COPY ui-app/ .

# Expose the port used by the Vite development server
EXPOSE 8100

# Use a default command, can be overridden in Docker compose.yml file
CMD ["npm", "run", "dev"]
