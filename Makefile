.PHONY: install run-api run-scheduler run-full test lint format docker-up docker-down clean

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
install:
	pip install -e ".[dev]"

# ---------------------------------------------------------------------------
# Run modes  (no Docker required — SQLite by default)
# ---------------------------------------------------------------------------
run-api:          ## Start the FastAPI server only
	DB_USE_SQLITE=true python -m src api

run-scheduler:    ## Start the data-collection scheduler only
	DB_USE_SQLITE=true python -m src scheduler

run-full:         ## Start API + scheduler together (SQLite)
	DB_USE_SQLITE=true python -m src full

# ---------------------------------------------------------------------------
# Docker (TimescaleDB stack)
# ---------------------------------------------------------------------------
docker-up:        ## Bring up full Docker stack
	docker compose up -d

docker-down:      ## Tear down Docker stack
	docker compose down

docker-logs:      ## Tail Docker logs
	docker compose logs -f

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------
test:             ## Run tests
	pytest tests/ -v

lint:             ## Lint with ruff
	ruff check src tests

format:           ## Auto-format with ruff
	ruff format src tests

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
clean:            ## Remove generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache dist build *.egg-info
