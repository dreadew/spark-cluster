# Spark Cluster with Jupyter and S3/Delta Lake

Docker Swarm-based Spark cluster with Jupyter Notebook, Postgres, MinIO (S3), and Delta Lake support, deployable via Ansible.

## Features

- Spark cluster (master + workers)  
- Jupyter Notebook with PySpark support  
- Postgres database  
- MinIO for S3 storage  
- Delta Lake support  
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
* `S3_BUCKETS` – Comma-separated list of buckets for raw data, Delta Lake, and warehouse (e.g., `raw-datasets,delta-lake,warehouse`)

## Deployment Flow

1. Copy `.env.example` to `.env` and configure variables.
2. Generate `JUPYTER_TOKEN` (optional; Ansible playbook can handle this automatically).
3. Deploy stack with Ansible:

```bash
ansible-playbook -i inventory.yml install_docker.yml
ansible-playbook -i inventory.yml setup_swarm.yml
ansible-playbook -i inventory.yml deploy_services.yml
```

4. Alternatively, run `make start-deploy` to execute all steps at once.

5. Load raw datasets into MinIO:

```bash
bash upload_raw_to_s3.sh
```

* This script uploads all files from the `raw_datasets/` folder, including all nested directories, into the `raw-datasets` bucket.

## Access

* Jupyter Notebook: `http://<manager-node-ip>:8888`
* Spark Master UI: `http://<manager-node-ip>:8080`
* MinIO Console: `http://<worker-node-ip>:9001`
* Postgres: `<worker-node-ip>:5432`
