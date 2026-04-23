# Codebase Hardening

Enforced quality gates for all changes.

- **Validate before commit**: `make validate` must pass (lint + types + tests)
- **Test coverage**: every new `src/**/*.py` module must have a corresponding `tests/test_*.py`
- **Function length**: max 50 lines per function — extract if over
- **No bare exceptions**: always log or re-raise with context
- **No unused code**: delete dead code, don't comment it out
