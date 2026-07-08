# Agencia-SEO — developer tasks.
# Everything runs through Poetry so the dev toolchain (pytest, ruff) is the one
# declared in pyproject.toml, not whatever happens to be on $PATH.

.DEFAULT_GOAL := help
.PHONY: help install test test-backend test-frontend lint format run

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (incl. dev group), Chromium, the Lighthouse CLI, and frontend deps
	poetry install
	poetry run playwright install chromium
	npm install
	npm --prefix frontend install

test: test-backend test-frontend ## Run every test suite (backend + frontend)

test-backend: ## Backend suite (pytest over tests/backend/)
	poetry run pytest

test-frontend: ## Frontend suite (vitest over tests/frontend/)
	npm --prefix frontend run test

lint: ## Lint with ruff (no changes written)
	poetry run ruff check .

format: ## Auto-format with ruff (imports + code)
	poetry run ruff check --select I --fix .
	poetry run ruff format .

run: ## Start the FastAPI dev server (reload) — backend.app.main:app
	poetry run fastapi dev backend/app/main.py
