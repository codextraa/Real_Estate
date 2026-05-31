FROM python:3.13-alpine AS deps

WORKDIR /home/django/app

RUN apk add --no-cache gcc musl-dev postgresql-dev libffi-dev

COPY ./backend/requirements_prod.txt .

RUN pip install --no-cache-dir --target=/home/django/app/packages -r requirements_prod.txt

FROM python:3.13-alpine AS builder

WORKDIR /home/django/app

COPY --from=deps /home/django/app/packages /usr/local/lib/python3.13/site-packages
COPY ./backend .

FROM python:3.13-alpine AS runner

RUN apk add --no-cache bash curl postgresql-client && \
    curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.alpine.sh' | distro=alpine version=3.20 bash && \
    apk add --no-cache infisical

RUN adduser -D django

WORKDIR /home/django/app

COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/

COPY --from=builder /home/django/app/backend/ ./backend/
COPY --from=builder /home/django/app/core_db/ ./core_db/
COPY --from=builder /home/django/app/auth_api/ ./auth_api/
COPY --from=builder /home/django/app/property_api/ ./property_api/
COPY --from=builder /home/django/app/static/ ./static/
COPY --from=builder /home/django/app/manage.py ./manage.py
COPY --from=builder /home/django/app/run.sh ./run.sh

RUN chmod +x ./run.sh && chown -R django:django /home/django/app

USER django

EXPOSE 8000
