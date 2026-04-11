.SILENT:
.ONESHELL:
.PHONY: setup setup_dev setup_espeak setup_piper setup_kokoro setup_stt setup_see setup_all clean validate lint_fix quick_validate lint_src lint_tests lint_md lint_links type_check test test_coverage speak wrap bump_patch bump_minor bump_major help
.DEFAULT_GOAL := help

# -- quiet mode (default: quiet; set VERBOSE=1 for full output) --
VERBOSE ?=
ifndef VERBOSE
  RUFF_QUIET   := --quiet
  PYTEST_QUIET := -q --tb=short --no-header
  COV_QUIET    := --cov-report=
endif


# MARK: SETUP


setup: ## Install cc-voice package (frozen lockfile)
	uv sync --frozen

setup_dev: ## Install with dev + test deps + all extras
	uv sync --all-extras

setup_espeak: ## Install espeak-ng + mpv (minimal, robotic TTS fallback)
	sudo apt-get update && sudo apt-get install -y espeak-ng mpv

setup_piper: ## Install Piper TTS (neural, good quality, ~60MB model)
	uv sync --extra piper

setup_kokoro: ## Install Kokoro TTS (best local quality, ~82MB model)
	uv tool install git+https://github.com/nazdridoy/kokoro-tts

setup_stt: ## Install STT deps (sounddevice + default engine)
	uv sync --extra stt

setup_see: ## Install /see deps (mss, Pillow, blake3). llama-cpp-python is a separate manual install — see output.
	uv sync --extra see
	@echo ""
	@echo "  /see scaffolding deps installed. llama-cpp-python is NOT in [see]"
	@echo "  extras because the correct wheel depends on your hardware. Install"
	@echo "  ONE of the following matching your platform:"
	@echo ""
	@echo "    CPU only (any OS):"
	@echo "      uv pip install 'llama-cpp-python' \\"
	@echo "        --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu"
	@echo ""
	@echo "    CUDA 12.4 (NVIDIA):"
	@echo "      uv pip install 'llama-cpp-python' \\"
	@echo "        --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124"
	@echo ""
	@echo "    Apple Silicon (Metal):"
	@echo "      CMAKE_ARGS='-DLLAMA_METAL=on' uv pip install llama-cpp-python"
	@echo ""
	@echo "  Then download a Qwen2.5-VL GGUF + mmproj, e.g."
	@echo "    https://huggingface.co/bartowski/Qwen2.5-VL-3B-Instruct-GGUF"
	@echo "  and set in .cc-voice.toml [vlm]:"
	@echo "    model_path = '/path/to/qwen2.5-vl-3b-instruct-q4_k_m.gguf'"
	@echo "    mmproj_path = '/path/to/mmproj-qwen2.5-vl-3b-instruct-f16.gguf'"

setup_all: setup_dev setup_espeak setup_piper setup_kokoro setup_stt setup_see ## Happy path: dev + all TTS + STT + /see
	@echo ""
	@echo "✓ cc-voice ready."
	@echo "  Try: cc-tts 'hello from claude code'"
	@echo "  Then in Claude Code: /speak --toggle"

clean: ## Remove venv + caches (preserves downloaded TTS/STT models)
	rm -rf .venv .pytest_cache .ruff_cache .coverage


# MARK: VALIDATION


validate: lint_src lint_tests type_check test ## Full validation (lint + type + test)
	echo "--- validate: all passed"

quick_validate: lint_src type_check ## Fast validation (lint + type)
	echo "--- quick_validate: passed"

lint_fix: ## Auto-fix lint and format issues
	echo "--- lint_fix"
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

lint_src: ## Lint and format src with ruff
	echo "--- lint_src$(if $(RUFF_QUIET), [quiet])"
	uv run ruff format --check $(RUFF_QUIET) src/
	uv run ruff check $(RUFF_QUIET) src/

lint_tests: ## Lint and format tests with ruff
	echo "--- lint_tests$(if $(RUFF_QUIET), [quiet])"
	uv run ruff format --check $(RUFF_QUIET) tests/
	uv run ruff check $(RUFF_QUIET) tests/

lint_md: ## Lint markdown files
	echo "--- lint_md"
	markdownlint '*.md' 'assets/**/*.md' '.claude/**/*.md' --fix

lint_links: ## Check for broken links with lychee
	echo "--- lint_links"
	if command -v lychee > /dev/null 2>&1; then
		lychee '*.md' 'assets/**/*.md' '.claude/**/*.md'
	else
		echo "lychee not installed — skipping"
	fi

type_check: ## Run pyright type checker
	echo "--- type_check"
	uv run pyright src/

test: ## Run pytest
	echo "--- test$(if $(PYTEST_QUIET), [quiet])"
	uv run pytest $(PYTEST_QUIET)

test_coverage: ## Run pytest with coverage (cc_tts + cc_stt)
	echo "--- test_coverage"
	uv run pytest --cov=cc_tts --cov=cc_stt --cov-report=term-missing $(COV_QUIET)


# MARK: RUN


speak: ## Test TTS: make speak TEXT="hello"
	uv run python -m cc_tts.speak $(TEXT)

wrap: ## Wrap command with live TTS (may deadlock under bwrap — see AGENT_LEARNINGS.md)
	uv run python -m cc_tts.pty_proxy $(CMD)


# MARK: VERSION


bump_patch: ## Bump patch version (0.3.0 → 0.3.1)
	uv run bump-my-version bump patch

bump_minor: ## Bump minor version (0.3.0 → 0.4.0)
	uv run bump-my-version bump minor

bump_major: ## Bump major version (0.3.0 → 1.0.0)
	uv run bump-my-version bump major


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
