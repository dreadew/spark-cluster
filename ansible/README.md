# Ansible Playbooks for Deployment

This directory contains Ansible playbooks for automated deployment of the Data Engineering stack to a Docker Swarm cluster.

## Files

- `inventory.yml` - Ansible inventory file (not tracked in git, create from `inventory.example.yml`)
- `inventory.example.yml` - Example inventory file template
- `install_docker.yml` - Installs Docker and Docker Compose on all nodes
- `setup_swarm.yml` - Initializes Docker Swarm cluster
- `deploy_services.yml` - Deploys the full stack to Swarm

## Usage

All playbooks should be run from the `services/` directory (parent directory):

```bash
# From services/ directory
ansible-playbook -i ansible/inventory.yml ansible/install_docker.yml
ansible-playbook -i ansible/inventory.yml ansible/setup_swarm.yml
ansible-playbook -i ansible/inventory.yml ansible/deploy_services.yml
```

Or use the Makefile shortcuts:

```bash
make install-docker
make setup-swarm
make deploy-services
# Or all at once:
make start-deploy
```

## Configuration

1. Copy `inventory.example.yml` to `inventory.yml`
2. Edit `inventory.yml` with your actual server IPs and SSH configuration
3. Ensure `.env` file is configured in the parent directory

## Notes

- All relative paths in playbooks (e.g., `./compose.yaml`) are resolved relative to the `services/` directory where ansible-playbook is executed
- Secrets are automatically rotated during deployment and saved to `services/secrets/`
