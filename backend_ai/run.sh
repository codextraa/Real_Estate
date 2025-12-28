#!/bin/sh
export INFISICAL_TOKEN=$(cat /run/secrets/infisical_token)
cd /run/secrets
infisical run --path="/Real-Estate/backend-ai" -- sh -c '
  cd /app &&
  
  if [ "$SERVICE_TYPE" = "ai-api" ]; then
    # Check if database exists, create it if not
    echo "Waiting for database '\''$DB_NAME'\'' to be created by main backend..."
    retries=5
    delay=2
    attempt=1
    while [ $attempt -le $retries ]; do
      if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        echo "✅ Database '\''$DB_NAME'\'' found!"
        break
      fi
      echo "Attempt $attempt/$retries: Database not found yet. Sleeping..."
      sleep $delay
      attempt=$((attempt + 1))
      [ $attempt -gt $retries ] && echo "❌ Error: Database creation timeout." && exit 1
    done

    # Migrate to db
    echo "Migrating AI models to database..."
    python manage.py migrate

    # Check environment and start appropriate server
    if [ "$DJANGO_ENV" = "production" ]; then
      # Start Gunicorn in production mode
      echo "Starting Gunicorn production server..."
      gunicorn backend_ai.wsgi:application --bind 0.0.0.0:8001 --workers=4 --threads=2 --timeout=120
    else
      # Start Django development server
      echo "Starting Django development server..."
      python manage.py runserver 0.0.0.0:8001
    fi
  else
    # Start AI workers
    echo "Waiting for AI-API to finish migrations..."
    retries=5
    delay=2
    attempt=1

    while [ $attempt -le $retries ]; do
      # python manage.py migrate --check returns 0 if all migrations are applied
      if python manage.py migrate --check > /dev/null 2>&1; then
        echo "✅ Migrations complete. Worker starting..."
        break
      fi

      echo "Attempt $attempt/$retries: Migrations pending. Sleeping ${delay}s..."
      sleep $delay
      attempt=$((attempt + 1))
      [ $attempt -gt $retries ] && echo "❌ Error: AI-API migrations timed out. Worker exiting..." && exit 1
    done

    # Defaulting to 4 workers if not set
    echo "Starting HPC Celery Workers (Concurrency: ${CELERY_WORKER_CONCURRENCY:-4})..."
    celery -A backend_ai worker --loglevel=info --concurrency=${CELERY_WORKER_CONCURRENCY:-4}
  fi
'
