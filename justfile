# On Windows just defaults to `sh`; use cmd.exe so no MSYS/Git-Bash is needed.
# Other platforms keep the default `sh -cu`.
set windows-shell := ["cmd.exe", "/c"]

install:
    uv pip install -e ".[dev]"
    playwright install chromium

format:
    ruff format src tests

lint:
    ruff check src tests

lint-fix:
    ruff check --fix src tests

test:
    pytest tests/unit -q --tb=short

test-integration:
    pytest tests/integration -q --tb=short

test-e2e:
    pytest tests/e2e -q --tb=short

test-all:
    pytest tests/ -q --tb=short

check: lint test

pre-commit-install:
    pre-commit install

[unix]
clean:
    rm -rf dist build .pytest_cache .ruff_cache playwright-report test-results
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type d -name "*.egg-info" -exec rm -rf {} +

[windows]
clean:
    -for %d in (dist build .pytest_cache .ruff_cache playwright-report test-results) do @if exist "%d" rmdir /s /q "%d"
    -for /d /r . %d in (__pycache__) do @if exist "%d" rmdir /s /q "%d"
    -for /d /r . %d in (*.egg-info) do @if exist "%d" rmdir /s /q "%d"

build:
    hatch build
