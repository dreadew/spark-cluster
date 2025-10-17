include .env
export $(shell sed 's/=.*//' .env)

STACK_NAME = spark_cluster
COMPOSE_FILE = compose.yaml
ENV_FILE = .env

SECRETS = JUPYTER_TOKEN

.PHONY: up down rotate-secrets redeploy-secrets

up:
	docker network create --driver overlay spark-net || true
	docker stack deploy -c $(COMPOSE_FILE) $(STACK_NAME)

down:
	docker stack rm $(STACK_NAME)

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