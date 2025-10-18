"""
Generate Trino SQL schemas from CSV files automatically.
Detects separators, column names, and generates proper CREATE TABLE statements.

Placed in services/scripts/ and reads .env for configuration (no external deps).
"""

import os
import csv
import re
from pathlib import Path
from typing import List, Tuple, Dict

# Base paths (relative to repository root where script is run)
RAW_DIR = Path(os.environ.get('S3_RAW_BUCKET', 'raw'))
SQL_OUTPUT = Path("sql/trino_schemas_generated.sql")


def load_env(env_paths=(".env", "services/.env")):
    """Load .env file(s) into environment without external deps.
    Looks for the first existing path in env_paths and loads KEY=VALUE lines.
    """
    for p in env_paths:
        path = Path(p)
        if path.exists():
            with path.open() as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln or ln.startswith('#'):
                        continue
                    if '=' not in ln:
                        continue
                    k, v = ln.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
            return True
    return False


def detect_separator(file_path: Path) -> Tuple[str, bool]:
    """Detect CSV separator by analyzing first non-empty line.
    Returns (separator_char, strip_spaces_flag).
    strip_spaces_flag indicates header fields are separated by comma+space patterns.
    """
    with file_path.open('r', encoding='utf-8', errors='ignore') as f:
        # read a few lines to find a non-empty header
        first_line = ''
        for _ in range(5):
            line = f.readline()
            if not line:
                break
            if line.strip():
                first_line = line
                break

    if not first_line:
        return ',', False

    # Count occurrences of common separators
    separators = {
        ',': first_line.count(','),
        ';': first_line.count(';'),
        '\t': first_line.count('\t'),
        '|': first_line.count('|'),
    }
    detected = max(separators.items(), key=lambda x: x[1])[0]

    strip_spaces = False
    if detected == ',' and ', ' in first_line:
        comma_space_count = first_line.count(', ')
        comma_count = first_line.count(',')
        if comma_count > 0 and (comma_space_count / comma_count) > 0.5:
            strip_spaces = True

    return detected, strip_spaces


def camel_to_snake(name: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()


def clean_column_name(col: str) -> str:
    """Clean and standardize column name."""
    col = col.strip()
    col = re.sub(r"\([^)]*\)", '', col)
    col = re.sub(r'[\s\-]+', '_', col)
    col = camel_to_snake(col)
    col = re.sub(r'_+', '_', col)
    col = col.strip('_')
    return col


def get_csv_columns(file_path: Path, separator: str, strip_spaces: bool) -> List[str]:
    """Extract column names from CSV header."""
    # csv.reader expects single-char delimiter; for tabs use '\t'
    delim = '\t' if separator == '\t' else separator[0]
    with file_path.open('r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f, delimiter=delim)
        header = next(reader)

    if strip_spaces:
        header = [h.strip() for h in header]

    columns = [clean_column_name(col) for col in header]
    return columns


def path_to_schema_table(file_path: Path, raw_dir: Path) -> Tuple[str, str]:
    """
    Generic conversion from file path to schema and table.
    Rule: schema = raw_<top-level-folder>
    If CSV is directly under that folder (raw/hotels/file.csv) -> table = filename stem
    If CSV is in a nested folder (raw/reviews/by_city/file.csv) -> table = "<top>-<parent>" e.g. reviews_by_city
    All names returned in snake_case.
    """
    rel_path = file_path.relative_to(raw_dir)
    parts = list(rel_path.parts)
    if not parts:
        raise ValueError("Invalid path relative to raw dir")

    top = parts[0]
    schema = f"raw_{top}"

    if len(parts) == 2:
        table = Path(parts[1]).stem
    else:
        parent = parts[-2]
        table = f"{top}_{parent}"

    # Clean
    table = clean_column_name(table)
    schema = clean_column_name(schema)
    return schema, table


def get_s3_path(file_path: Path, raw_dir: Path, s3_bucket: str) -> str:
    rel_path = file_path.relative_to(raw_dir)
    parts = list(rel_path.parts[:-1])
    s3_path = f"s3://{s3_bucket}/{'/'.join(parts)}/"
    return s3_path


def generate_create_table(
    schema: str,
    table: str,
    columns: List[str],
    s3_location: str,
    separator: str
) -> str:
    col_defs = ",\n    ".join([f"{col} VARCHAR" for col in columns])
    sep_param = ""
    if separator != ',':
        if separator == '\t':
            sep_param = f",\n    csv_separator = '\\t'"
        else:
            sep_param = f",\n    csv_separator = '{separator}'"

    sql = f"""CREATE TABLE IF NOT EXISTS {table} (
    {col_defs}
)
WITH (
    external_location = '{s3_location}',
    format = 'CSV',
    skip_header_line_count = 1{sep_param}
);"""
    return sql


def collect_csv_files(raw_dir: Path) -> Dict[str, List[Path]]:
    schemas = {}
    for csv_file in raw_dir.rglob("*.csv"):
        schema, table = path_to_schema_table(csv_file, raw_dir)
        schemas.setdefault(schema, []).append(csv_file)
    return schemas


def generate_sql():
    # Load env (S3 bucket name etc.)
    load_env()
    s3_bucket = os.environ.get('S3_RAW_BUCKET', 'raw')

    print("🔍 Scanning CSV files...")
    schemas_files = collect_csv_files(RAW_DIR)

    sql_output = []
    sql_output.append("-- " + "=" * 60)
    sql_output.append("-- AUTO-GENERATED TRINO SCHEMAS FOR RAW DATA")
    sql_output.append("-- Generated from CSV files in raw/ directory")
    sql_output.append("-- " + "=" * 60)
    sql_output.append("")

    processed_tables = set()

    for schema in sorted(schemas_files.keys()):
        sql_output.append(f"-- Schema: {schema}")
        sql_output.append(f"CREATE SCHEMA IF NOT EXISTS hive.{schema};")
        sql_output.append(f"USE hive.{schema};")
        sql_output.append("")

        files = schemas_files[schema]
        for csv_file in sorted(files):
            schema_name, table_name = path_to_schema_table(csv_file, RAW_DIR)
            table_key = f"{schema_name}.{table_name}"
            if table_key in processed_tables:
                continue
            processed_tables.add(table_key)

            print(f"  Processing: {csv_file}")
            separator, strip_spaces = detect_separator(csv_file)
            print(f"    Separator: {repr(separator)}, strip_spaces={strip_spaces}")

            try:
                columns = get_csv_columns(csv_file, separator, strip_spaces)
                print(f"    Columns: {len(columns)}")
            except Exception as e:
                print(f"    ⚠️  Error reading columns: {e}")
                continue

            s3_path = get_s3_path(csv_file, RAW_DIR, s3_bucket)
            print(f"    S3: {s3_path}")

            create_table_sql = generate_create_table(
                schema_name,
                table_name,
                columns,
                s3_path,
                separator,
            )

            sql_output.append(f"-- Table: {table_name}")
            sql_output.append(f"-- Source: {csv_file}")
            sql_output.append(f"-- Columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
            sql_output.append(create_table_sql)
            sql_output.append("")

        sql_output.append("")

    SQL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with SQL_OUTPUT.open('w') as f:
        f.write('\n'.join(sql_output))

    print(f"\n✅ Generated SQL schema: {SQL_OUTPUT}")
    print(f"📊 Total schemas: {len(schemas_files)}")
    print(f"📋 Total tables: {len(processed_tables)}")


if __name__ == "__main__":
    generate_sql()
