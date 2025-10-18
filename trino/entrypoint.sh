#!/bin/bash
set -e

echo "Generating Trino catalog files from templates..."

substitute_vars() {
    local input_file=$1
    local output_file=$2
    
    eval "cat <<EOF
$(cat "$input_file")
EOF
" > "$output_file"
}

substitute_vars /etc/trino/catalog-templates/hive.properties.template /etc/trino/catalog/hive.properties
substitute_vars /etc/trino/catalog-templates/delta.properties.template /etc/trino/catalog/delta.properties

echo "Catalog files generated:"
echo "  - hive.properties"
echo "  - delta.properties"

# Show generated content for debugging (optional, remove in production)
# echo ""
# echo "=== hive.properties ==="
# cat /etc/trino/catalog/hive.properties
# echo ""
# echo "=== delta.properties ==="
# cat /etc/trino/catalog/delta.properties
# echo ""

exec /usr/lib/trino/bin/run-trino