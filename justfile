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
    rm -rf dist build .pytest_cache .ruff_cache playwright-report test-results
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type d -name "*.egg-info" -exec rm -rf {} +

build:
    hatch build
