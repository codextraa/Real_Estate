#!/bin/sh
export INFISICAL_TOKEN=$(cat /run/secrets/infisical_token)
cd /run/secrets
infisical run --path="/Real-Estate/frontend" -- sh -c '
    cd /app
    
    # Handle local CA certificate if provided
    if [ -n "$local_ca" ]; then
        echo "$local_ca" > /tmp/local-ca.pem
        export NODE_EXTRA_CA_CERTS=/tmp/local-ca.pem
    fi
    
    # Check environment and start appropriate server
    if [ "$NODE_ENV" = "production" ]; then
        echo "Starting Next.js in Standalone Production mode..."
        export PORT=${PORT:-3000}
        export HOSTNAME=${HOSTNAME:-"0.0.0.0"}
        node .next/standalone/server.js
    else
        echo "Starting Next.js in development mode..."
        npm run dev
    fi
'