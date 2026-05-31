FROM python:3.13-alpine AS deps

WORKDIR /home/django_ai/app

RUN apk add --no-cache \
    gcc \
    g++ \
    gfortran \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openblas-dev \
    lapack-dev

COPY ./backend_ai/requirements_prod.txt .

RUN pip install --no-cache-dir --target=/home/django_ai/app/packages -r requirements_prod.txt

FROM python:3.13-alpine AS builder

WORKDIR /home/django_ai/app

COPY --from=deps /home/django_ai/app/packages /usr/local/lib/python3.13/site-packages
COPY ./backend_ai .

FROM python:3.13-alpine AS runner

RUN apk add --no-cache \
    bash \
    curl \
    postgresql-client \
    libstdc++ \
    openblas \
    lapack && \
    curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.alpine.sh' | distro=alpine version=3.20 bash && \
    apk add --no-cache infisical

RUN adduser -D django_ai

WORKDIR /home/django_ai/app

COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/

COPY --from=builder /home/django_ai/app/backend_ai/ ./backend_ai/
COPY --from=builder /home/django_ai/app/core_db_ai/ ./core_db_ai/
COPY --from=builder /home/django_ai/app/chat_api/ ./chat_api/
COPY --from=builder /home/django_ai/app/report_api/ ./report_api/
COPY --from=builder /home/django_ai/app/static_ai/ ./static_ai/
COPY --from=builder /home/django_ai/app/manage.py ./manage.py
COPY --from=builder /home/django_ai/app/run.sh ./run.sh

RUN chmod +x ./run.sh && chown -R django_ai:django_ai /home/django_ai/app

USER django_ai

EXPOSE 8001
