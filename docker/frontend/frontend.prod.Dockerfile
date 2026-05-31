FROM node:24-alpine AS deps

RUN apk add --no-cache libc6-compat

WORKDIR /home/nextjs/app

COPY ./frontend/package.json ./frontend/package-lock.json* ./

RUN npm ci

FROM node:24-alpine AS builder

WORKDIR /home/nextjs/app

COPY --from=deps /home/nextjs/app/node_modules ./node_modules
COPY ./frontend .

RUN npm run build

FROM node:24-alpine AS runner

RUN apk add --no-cache bash curl && \
    curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.alpine.sh' | distro=alpine version=3.20 bash && \
    apk add --no-cache infisical

RUN adduser -D nextjs

WORKDIR /home/nextjs/app

COPY --from=builder --chown=nextjs:nextjs /home/nextjs/app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /home/nextjs/app/public ./public
COPY --from=builder --chown=nextjs:nextjs /home/nextjs/app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nextjs /home/nextjs/app/run.sh ./run.sh

RUN chmod +x ./run.sh && chown -R nextjs:nextjs /home/nextjs/app

USER nextjs

EXPOSE 3000
