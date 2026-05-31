#!/bin/sh
export INFISICAL_TOKEN=$(cat /run/secrets/infisical_token)
cd /run/secrets
infisical run --path="/Real-Estate/backend-ai" -- sh -c '
  { if [ "$DJANGO_ENV" = "production" ]; then cd /home/django_ai/app; else cd /app; fi; } &&

  export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
  
  if [ "$SERVICE_TYPE" = "ai-api" ]; then
    echo "Running in AI-API mode..."
    echo "Verifying that main backend has provisioned and ready the database..."
    
    retries=5
    delay=3
    attempt=1
    while [ $attempt -le $retries ]; do
      python -c "
import sys, psycopg2
try:
    psycopg2.connect(
        dbname=\"$DB_NAME\", 
        user=\"$DB_USER\", 
        password=\"$DB_PASSWORD\", 
        host=\"$DB_HOST\", 
        port=\"$DB_PORT\", 
        connect_timeout=3
    )
except Exception as e:
    sys.stderr.write(f\"Database connection failed: {e}\n\")
    sys.exit(1)
"

      if [ $? -eq 0 ]; then
        echo "✅ Database '\''$DB_NAME'\'' is ready and accepting credentials!"
        break
      fi

      echo "Attempt $attempt/$retries: Database not fully ready yet. Sleeping ${delay}s..."
      sleep $delay
      attempt=$((attempt + 1))
      if [ $attempt -gt $retries ]; then
        echo "❌ Error: Database ready check timed out. Exiting..." >&2
        exit 1
      fi
    done

    # Check environment and start appropriate server
    if [ "$DJANGO_ENV" = "production" ]; then
      echo "Migrating AI models to database..."
      python manage.py migrate --noinput

      echo "Collecting AI administration static assets..."
      python manage.py collectstatic --noinput

      echo "Starting Gunicorn with Uvicorn workers (ASGI Production on port 8001)..."
      gunicorn backend_ai.asgi:application \
               --bind 0.0.0.0:8001 \
               --workers 4 \
               --worker-class uvicorn.workers.UvicornWorker \
               --timeout 120 \
               --access-logfile - \
               --error-logfile -
    else
      echo "Migrating AI models to database..."
      python manage.py migrate

      # DEVELOPMENT: Standard Uvicorn with auto-reload
      echo "Starting Uvicorn development server..."
      uvicorn backend_ai.asgi:application --host 0.0.0.0 --port 8001 --reload
    fi
  else
    # Start AI workers
    echo "Waiting for AI-API to finish migrations..."
    retries=10
    delay=3
    attempt=1

    while [ $attempt -le $retries ]; do
      # python manage.py migrate --check returns 0 if all migrations are applied
      python manage.py migrate --check
      
      if [ $? -eq 0 ]; then
        echo "✅ Migrations complete. Worker starting..."
        break
      fi

      echo "Attempt $attempt/$retries: Migrations pending. Sleeping ${delay}s..."
      sleep $delay
      attempt=$((attempt + 1))
      [ $attempt -gt $retries ] && echo "❌ Error: AI-API migrations timed out. Worker exiting..." && exit 1
    done

    if [ "$DJANGO_ENV" = "production" ]; then
      echo "Starting Production Celery Workers (Thread Pool, Concurrency: ${CELERY_WORKER_CONCURRENCY:-4})..."
      celery -A backend_ai worker \
             --loglevel=info \
             --pool=gevent \
             --concurrency=${CELERY_WORKER_CONCURRENCY:-4}
    else
      echo "Starting Development Celery Workers (Prefork, Concurrency: ${CELERY_WORKER_CONCURRENCY:-4})..."
      celery -A backend_ai worker --loglevel=info --concurrency=${CELERY_WORKER_CONCURRENCY:-4}
    fi
  fi
'
