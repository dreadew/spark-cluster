#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# SQL files are in services/sql/ (one level up from scripts/)
SQL_DIR="$(dirname "$SCRIPT_DIR")/sql"

echo "Creating Trino schemas..."

if ! docker ps | grep -q trino; then
    echo "Error: Trino container is not running"
    echo "Start the services first: make -f Makefile.local up"
    exit 1
fi

execute_sql() {
    local sql_file=$1
    local description=$2
    
    echo ""
    echo "Executing: $description"
    echo "File: $sql_file"
    
    if [ ! -f "$sql_file" ]; then
        echo "Error: SQL file not found: $sql_file"
        exit 1
    fi
    
    docker exec -i trino trino --file=/dev/stdin < "$sql_file"
    
    if [ $? -eq 0 ]; then
        echo "✓ $description completed successfully"
    else
        echo "✗ $description failed"
        exit 1
    fi
}

echo "Waiting for Trino to be ready..."
sleep 5

max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec trino trino --execute "SELECT 1" > /dev/null 2>&1; then
        echo "✓ Trino is ready"
        break
    fi
    attempt=$((attempt + 1))
    echo "Waiting for Trino... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "Error: Trino did not become ready in time"
    exit 1
fi

execute_sql "$SQL_DIR/trino_schemas.sql" "Creating raw data schemas"

execute_sql "$SQL_DIR/prod_trino_schemas.sql" "Creating production schemas"

echo ""
echo "=========================================="
echo "All Trino schemas created successfully!"
echo "=========================================="
echo ""
echo "Available schemas:"
docker exec trino trino --execute "SHOW SCHEMAS IN hive" | grep -E "raw_|prod_"