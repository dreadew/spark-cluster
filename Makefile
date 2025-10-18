include .env
export $(shell sed 's/=.*//' .env)

STACK_NAME = spark_cluster
COMPOSE_FILE = compose.yaml
ENV_FILE = .env

SECRETS = JUPYTER_TOKEN SUPERSET_SECRET_KEY

.PHONY: install-docker setup-swarm deploy-services deploy start-deploy up-stack down-stack deploy-local up-local down-local rotate-secrets redeploy-secrets setup-superset upload-raw-to-s3 create-trino-schemas generate-schemas

# =================================
# PRODUCTION DEPLOYMENT COMMANDS
# =================================

install-docker:
	ansible-playbook -i ansible/inventory.yml ansible/install_docker.yml

setup-swarm:
	ansible-playbook -i ansible/inventory.yml ansible/setup_swarm.yml

deploy-services:
	ansible-playbook -i ansible/inventory.yml ansible/deploy_services.yml

deploy:
	docker stack deploy -c compose.yaml de_stack

start-deploy:
	make install-docker
	make setup-swarm
	make deploy-services

# =================================
# DOCKER SWARM STACK COMMANDS
# =================================

up-stack:
	docker network create --driver overlay spark-net || true
	docker stack deploy -c $(COMPOSE_FILE) $(STACK_NAME)

down-stack:
	docker stack rm $(STACK_NAME)

# =================================
# LOCAL DEVELOPMENT COMMANDS
# =================================

deploy-local:
	make down-local
	make up-local
	sleep 5
	make upload-raw-to-s3
	make generate-schemas
	make create-trino-schemas
	make setup-superset

up-local:
	docker compose -f compose.local.yaml up -d --build

down-local:
	docker compose -f compose.local.yaml down -v

# =================================
# AUTO CONFIGURATION
# =================================

generate-schemas:
	python3 scripts/generate_trino_schemas.py

setup-superset:
	docker exec -it superset python /app/setup_datasets.py

create-trino-schemas:
	bash scripts/create_trino_schemas.sh

upload-raw-to-s3:
	bash scripts/upload_raw_to_s3.sh

# =================================
# SECRET MANAGEMENT
# =================================

rotate-secrets:
	@echo "Rotating secrets in $(ENV_FILE)..."
	@tmp_file=$$(mktemp); \
	cp $(ENV_FILE) $$tmp_file; \
	for key in $(SECRETS); do \
		echo "→ Rotating $$key"; \
		sed -i.bak "/^$$key=/d" $$tmp_file; \
		echo "$$key=$$(openssl rand -hex 32)" >> $$tmp_file; \
	done; \
	mv $$tmp_file $(ENV_FILE); \
	rm -f $(ENV_FILE).bak; \
	echo "Secrets rotated: $(SECRETS)"

redeploy-secrets: down rotate-secrets up