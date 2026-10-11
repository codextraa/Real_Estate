FROM node:22-alpine

WORKDIR /app
COPY ./frontend/package.json ./frontend/package-lock.json* ./

RUN npm install
RUN apk add --no-cache bash wget && \
    wget -qO- 'https://artifacts-cli.infisical.com/setup.apk.sh' | sh && \
    apk add --no-cache infisical

EXPOSE 3000
