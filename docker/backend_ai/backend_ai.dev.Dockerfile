FROM python:3.12-slim

WORKDIR /app
COPY ./backend_ai/requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    postgresql-client-17 \
    && curl -1sLf 'https://artifacts-cli.infisical.com/setup.deb.sh' | bash \
    && apt-get install -y infisical \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8001
