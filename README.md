# Spark Cluster with Jupyter and S3/Delta Lake

Docker Swarm-based Spark cluster with Jupyter Notebook, Postgres, MinIO (S3), and Delta Lake support, deployable via Ansible.

## Features

- Spark cluster (master + workers)
- Jupyter Notebook with PySpark support
- Postgres database
- MinIO for S3 storage
- Delta Lake support
- Trino query engine with Delta Lake connector
- Apache Superset for data visualization
- Valkey for caching
- Automatic deployment via Ansible  

## Makefile Targets

### Local development
```bash
make -f Makefile.local up      # Start local Docker Compose
make -f Makefile.local down    # Stop local Docker Compose
````

### Production / Swarm deployment

```bash
make -f Makefile.prod install-docker      # Install Docker on remote hosts
make -f Makefile.prod setup-swarm         # Initialize Docker Swarm cluster
make -f Makefile.prod deploy-services     # Deploy stack via Ansible
make -f Makefile.prod deploy              # Deploy Docker stack directly
make -f Makefile.prod start-deploy        # All-in-one: install Docker + setup Swarm + deploy services
```

## Environment Variables

Use `.env` file or `.env.example` as template:

* `SPARK_URL` – Spark Master URL
* `JUPYTER_TOKEN` – Jupyter Notebook token (generated via `openssl rand -hex 32`)
* `DB_CONNECTION_STRING` – Postgres connection string
* `S3_PROTOCOL`, `S3_HOST`, `S3_EXTERNAL_HOST`, `S3_PORT` – S3/MinIO host configuration
* `S3_ACCESS_KEY`, `S3_SECRET_KEY` – S3 credentials
* `S3_BUCKETS` – Comma-separated list of S3 buckets (e.g., `raw,prod,warehouse`)
* `S3_RAW_BUCKET` – Bucket for raw data (default: `raw`)
* `S3_PROD_BUCKET` – Bucket for production data in Delta Lake format (default: `prod`)
* `S3_WAREHOUSE_BUCKET` – Bucket for Hive warehouse (default: `warehouse`)
* `SUPERSET_SECRET_KEY` – Superset secret key for session encryption
* `SUPERSET_ADMIN_USERNAME`, `SUPERSET_ADMIN_PASSWORD` – Default Superset admin credentials
* `SUPERSET_DB_NAME`, `SUPERSET_DB_USER`, `SUPERSET_DB_PASSWORD` – Superset metadata database

## Deployment Flow

1. Copy `.env.example` to `.env` and configure variables.
2. Generate `JUPYTER_TOKEN` (optional; Ansible playbook can handle this automatically).
3. Deploy stack with Ansible:

```bash
ansible-playbook -i ansible/inventory.yml ansible/install_docker.yml
ansible-playbook -i ansible/inventory.yml ansible/setup_swarm.yml
ansible-playbook -i ansible/inventory.yml ansible/deploy_services.yml
```

4. Alternatively, run `make start-deploy` to execute all steps at once.

5. Load raw datasets into MinIO:

```bash
bash upload_raw_to_s3.sh
```

6. Create Trino schemas (raw and production):

```bash
bash create_trino_schemas.sh
```

This script creates:
* Raw data schemas (CSV format in `s3://raw/`)
* Production schemas (Delta Lake format in `s3://prod/`)

## Project Structure

### 📁 `sql/`
Contains example generated Trino SQL schemas:
- `trino_schemas.sql` - Raw data schemas (CSV-backed tables)
- `prod_trino_schemas.sql` - Production schemas (Delta Lake format)
- `trino_schemas_generated.sql` - Auto-generated schemas from CSV files

These schemas demonstrate the **Medallion Architecture** pattern:
- **Raw layer** (`s3://raw/`) - Unprocessed CSV data
- **Production layer** (`s3://prod/`) - Cleaned Delta Lake tables
- **Gold layer** (optional) - Aggregated analytics tables

### 📁 `architecture/`
Contains documentation and examples of data structure:
- `data.md` - Detailed schema documentation
- Dataset examples and data model descriptions
- Architecture diagrams and design decisions

The examples use real hotel booking and review datasets to demonstrate:
- Multi-format data ingestion (CSV → Delta)
- Schema evolution and data quality patterns
- Analytics query optimization techniques

For detailed schema documentation, see [`architecture/data.md`](architecture/data.md).

## Access

* Superset UI: `http://<manager-node-ip>:8089` (admin/admin)
* Trino CLI: `docker exec -it trino trino`
* Jupyter Notebook: `http://<manager-node-ip>:8888`
* Spark Master UI: `http://<manager-node-ip>:8080`
* MinIO Console: `http://<worker-node-ip>:9001`
* Postgres: `<worker-node-ip>:5432`
