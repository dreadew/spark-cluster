#!/usr/bin/env bash
set -euo pipefail

# Simplified idempotent entrypoint for Postgres: only creates 'superset' database if missing.

# Function to create superset DB idempotently
create_superset_db() {
  echo "Running idempotent superset database creation..."

  # Wait for Postgres to be ready
  export PGPASSWORD="${POSTGRES_PASSWORD:-}"
  for i in {1..30}; do
    if pg_isready -h localhost -p 5432 -U "${POSTGRES_USER}" >/dev/null 2>&1; then
      echo "Postgres is ready"
      break
    fi
    echo "Waiting for Postgres... ($i)"
    sleep 1
  done

  # Create database 'superset' only if it doesn't exist
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'EOSQL'
SELECT 'CREATE DATABASE superset'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'superset')\gexec
EOSQL

  echo "Superset database is ready (idempotent check completed)"
}

# If the first arg is 'postgres' or starts with '-', delegate to official entrypoint
if [ "$#" -gt 0 ] && { [ "$1" = 'postgres' ] || [[ "$1" = -* ]]; }; then
  echo "Delegating to official postgres entrypoint..."
  
  # Start official entrypoint in background
  docker-entrypoint.sh "$@" &
  PG_PID=$!

  # Wait a moment for postgres to start, then run init
  sleep 2
  create_superset_db

  # Wait for postgres process to complete (keep container running)
  wait $PG_PID
else
  # Not postgres command, just exec it
  exec "$@"
fi
