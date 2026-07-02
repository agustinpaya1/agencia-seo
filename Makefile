# Agencia-SEO — developer tasks.
# Everything runs through Poetry so the dev toolchain (pytest, ruff) is the one
# declared in pyproject.toml, not whatever happens to be on $PATH.

.DEFAULT_GOAL := help
.PHONY: help install test lint format run

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (incl. dev group)
	poetry install

test: ## Run the test suite
	poetry run pytest

lint: ## Lint with ruff (no changes written)
	poetry run ruff check .

format: ## Auto-format with ruff (imports + code)
	poetry run ruff check --select I --fix .
	poetry run ruff format .

run: ## Start the FastAPI dev server (reload) — backend.app.main:app
	poetry run fastapi dev backend/app/main.py
