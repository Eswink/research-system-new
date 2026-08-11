VERSION := $(strip $(file <VERSION))
UV ?= uv
PNPM ?= pnpm
RUNNER := .cursor/skills/cursor-framework-check/scripts/run_all_checks.py
UV_PYTHON := $(UV) run --frozen --no-sync python -B
FRAMEWORK_ZIP := ../system-specification-cursor-framework-v$(VERSION).zip

export PYTHONUTF8 := 1
export PYTHONIOENCODING := utf-8

.PHONY: bootstrap lock-check quality quality-python quality-typescript validate-spec validate-cursor validate-learning validate-all framework-release framework-package

lock-check:
	$(UV) lock --check
	$(PNPM) install --frozen-lockfile --lockfile-only

bootstrap:
	$(UV) lock --check
	$(UV) sync --frozen --dev
	$(PNPM) install --frozen-lockfile

quality-python:
	$(UV_PYTHON) $(RUNNER) --profile python

quality-typescript:
	$(UV_PYTHON) $(RUNNER) --profile typescript

validate-spec:
	$(UV_PYTHON) .cursor/skills/system-spec-check/scripts/validate_bundle.py

validate-cursor:
	$(UV_PYTHON) $(RUNNER) --profile framework

validate-learning:
	$(UV_PYTHON) .cursor/skills/learning-check/scripts/validate_cursor_learning.py
	$(UV_PYTHON) .cursor/skills/learning-check/scripts/run_cursor_learning_evals.py

quality validate-all:
	$(UV_PYTHON) $(RUNNER) --profile m0 --keep-going

framework-release:
	$(UV_PYTHON) .cursor/skills/framework-release/scripts/release_cursor_framework.py --version $(VERSION)

framework-package: framework-release
	$(UV_PYTHON) .cursor/skills/framework-release/scripts/package_cursor_framework.py --version $(VERSION) --output $(FRAMEWORK_ZIP)