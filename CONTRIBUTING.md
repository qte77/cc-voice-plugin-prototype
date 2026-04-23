# Contributing

## Setup

```bash
uv sync --all-extras        # install all deps
```

## Development Workflow

1. Create a feature branch off `main`
2. Make changes, keeping functions under 50 lines
3. Add tests for new modules (`tests/test_*.py`)
4. Run validation: `make validate` (lint + types + tests)
5. Open a PR — squash merge only

## Commands

| Command | Purpose |
|---------|---------|
| `make validate` | Full validation (lint + types + tests) |
| `make lint_fix` | Auto-fix lint and format issues |
| `make test` | Run tests only |
| `make test_coverage` | Tests with coverage report |

## Conventions

- **Config**: pydantic `BaseSettings` in each module's `config.py`
- **Testing**: pytest, one `test_*.py` per `src/**/*.py` module
- **Commits**: `type(scope): message` (e.g., `feat(stt): add whisper engine`)
- **Dependencies**: `uv` only, never `pip`
