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

# Templates. Two invocations because `profile` is one global setting and the
# cotton tree is Django template language while the jinja tree is Jinja2.
# Settings live in `[tool.djlint]`; `prek` runs the same thing on commit.
format-templates:
    djlint src/cf_ui/templates/cotton --profile=django --reformat
    djlint src/cf_ui/templates/jinja --profile=jinja --extension=jinja --reformat

lint-templates:
    djlint src/cf_ui/templates/cotton --profile=django
    djlint src/cf_ui/templates/jinja --profile=jinja --extension=jinja

test:
    pytest tests/unit -q --tb=short

# The Tailwind plugin's own suite. `just test` runs it too, via a pytest
# wrapper that skips when node is missing; this recipe never skips.
test-js:
    node --test --test-reporter=spec "tests/js/**/*.test.mjs"

# The vendored plugin through a real Tailwind build: the good paths compile,
# the CSS actually lands, and an unknown composition exits non-zero. `test-js`
# covers the same plugin but never invokes Tailwind, so it cannot notice the
# contract changing underneath it.
test-tailwind:
    npm ci --prefix tests/tailwind
    node --test --test-reporter=spec tests/tailwind/build.test.mjs

# Rebuild cf_ui_axes.css and cf_ui_axes.json from axes.py.
axes:
    python -m cf_ui.axes

primitives:
    python -m cf_ui.primitives

test-integration:
    pytest tests/integration -q --tb=short

test-e2e:
    pytest tests/e2e -q --tb=short

# Separate pytest invocations, not `pytest tests/` — django-cotton's
# AppConfig.ready() mutates settings.TEMPLATES in place and resets Django's
# global template-engine cache the moment it's in INSTALLED_APPS (see
# tests/integration/cotton_app/settings.py), so any single process that
# combines the integration tier with the unit tier leaks real cotton
# compilation into the unit tier's render_to_string calls. Matches how
# .github/workflows/ci.yml already runs each tier as its own step.
test-all:
    pytest tests/unit -q --tb=short
    pytest tests/integration -q --tb=short
    pytest tests/e2e -q --tb=short

check: lint lint-templates test

# Serve the docs site with live reload at http://127.0.0.1:8000
docs:
    mkdocs serve

# Build the site exactly as CI does — --strict fails on a dead internal link
# or a page missing from nav, which is the whole point of running it locally.
docs-build:
    mkdocs build --strict

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
