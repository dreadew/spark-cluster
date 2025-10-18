#!/bin/bash
set -e

echo "Checking if superset database exists..."

# Create superset database only if it doesn't exist (idempotent)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE superset'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'superset')\gexec
EOSQL

echo "Superset database is ready"
