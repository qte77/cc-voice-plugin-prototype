.SILENT:
.ONESHELL:
.PHONY: setup setup_dev validate quick_validate lint type_check test test_coverage speak help
.DEFAULT_GOAL := help


# MARK: SETUP


setup: ## Install cc-tts package
	uv pip install -e .

setup_dev: ## Install with dev + test deps
	uv pip install -e ".[dev,test]"


# MARK: VALIDATION


validate: lint type_check test ## Full validation (lint + type + test)

quick_validate: lint type_check ## Fast validation (lint + type)

lint: ## Run ruff linter + formatter check
	ruff check src/ tests/
	ruff format --check src/ tests/

type_check: ## Run pyright type checker
	pyright src/

test: ## Run pytest
	pytest

test_coverage: ## Run pytest with coverage
	pytest --cov=cc_tts --cov-report=term-missing


# MARK: RUN


speak: ## Test TTS: make speak TEXT="hello"
	python -m cc_tts.speak $(TEXT)


# MARK: HELP


help: ## Show available recipes grouped by section
	@echo "Usage: make [recipe]"
	@echo ""
	@awk '/^# MARK:/ { \
		section = substr($$0, index($$0, ":")+2); \
		printf "\n\033[1m%s\033[0m\n", section \
	} \
	/^[a-zA-Z0-9_-]+:.*?##/ { \
		helpMessage = match($$0, /## (.*)/); \
		if (helpMessage) { \
			recipe = $$1; \
			sub(/:/, "", recipe); \
			printf "  \033[36m%-22s\033[0m %s\n", recipe, substr($$0, RSTART + 3, RLENGTH) \
		} \
	}' $(MAKEFILE_LIST)
