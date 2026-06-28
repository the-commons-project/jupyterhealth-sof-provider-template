.PHONY: init install run run-docker test

# Interactively create .env (non-destructive). Or just: cp .env.example .env
init:
	bash scripts/init-env.sh

# Editable install with the test extra.
install:
	pip install -e ".[test]"

# Serve the dashboard with Voilà (reads .env via jupyter_server_config.py).
run:
	jupyter server --config=jupyter_server_config.py

# Or run the whole thing in a container.
run-docker:
	docker compose up --build

test:
	pytest
