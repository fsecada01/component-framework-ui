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

clean:
    rm -rf dist .pytest_cache __pycache__ src/cf_ui/__pycache__

build:
    hatch build
