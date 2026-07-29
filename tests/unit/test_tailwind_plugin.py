"""The Python half of the Tailwind plugin's guarantees (issue #7).

Two jobs:

1. Run the plugin's own ``node --test`` suite, so a Python-only ``pytest`` run
   still exercises the JS. CI runs ``node --test`` directly as well — the
   skip below is a local convenience, not the only path.
2. **Prove the two generators agree.** ``axes.py`` renders ``cf_ui_axes.css``;
   the plugin renders the same rules inside the CSS build. #7 asks for one
   source of truth, and the JSON export only guarantees they read the same
   *input*. This compares their *output*, declaration by declaration, which is
   what would actually break a consuming app if it drifted.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

import pytest

from cf_ui.axes import DEFAULT_VALUE_SETS, render_axis_css

REPO_ROOT = Path(__file__).resolve().parents[2]
# A glob, not a directory: node >=25 reads a bare directory as a module to run.
# The TAP reporter is requested explicitly so the pass count below is parseable
# regardless of node's default reporter for the current version and TTY state.
JS_TEST_GLOB = "tests/js/**/*.test.mjs"
PLUGIN_PATH = REPO_ROOT / "src" / "cf_ui" / "static" / "cf_ui" / "cf_ui_tailwind_plugin.mjs"
DEFINITION_PATH = REPO_ROOT / "src" / "cf_ui" / "static" / "cf_ui" / "cf_ui_axes.json"

NODE = shutil.which("node")
requires_node = pytest.mark.skipif(
    NODE is None,
    reason="node is not installed — CI runs `node --test tests/js/` as its own step",
)


def _run_node(script: str) -> str:
    """Evaluate a module-scoped snippet against the plugin and return stdout."""
    result = subprocess.run(  # noqa: S603
        [NODE, "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        raise AssertionError(f"node failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout


# --- the JS suite ----------------------------------------------------------


@requires_node
def test_the_node_test_suite_passes():
    result = subprocess.run(  # noqa: S603
        [NODE, "--test", "--test-reporter=tap", JS_TEST_GLOB],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    sys.stdout.write(result.stdout)
    sys.stdout.write(result.stderr)
    assert result.returncode == 0, "node --test tests/js/ failed"


@requires_node
def test_the_node_suite_is_not_empty():
    """A passing run of zero tests is the failure mode this guards against."""
    result = subprocess.run(  # noqa: S603
        [NODE, "--test", "--test-reporter=tap", JS_TEST_GLOB],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    match = re.search(r"^# pass (\d+)$", result.stdout, re.MULTILINE)
    assert match, f"could not read a pass count from node's output:\n{result.stdout}"
    assert int(match.group(1)) > 20, "the JS suite shrank unexpectedly"


# --- cross-language parity -------------------------------------------------

_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_RULE = re.compile(r"([^{}]+?)\{([^{}]*)\}", re.DOTALL)


def _declarations(css: str) -> dict[str, dict[str, str]]:
    """Parse flat CSS into ``{selector: {property: value}}``."""
    parsed: dict[str, dict[str, str]] = {}
    for selector, body in _RULE.findall(css):
        tokens = {}
        for line in body.split(";"):
            if ":" not in line:
                continue
            name, _, value = line.partition(":")
            tokens[name.strip()] = value.strip()
        if tokens:
            parsed[selector.strip()] = tokens
    return parsed


def _python_rules() -> tuple[dict, dict]:
    """Split the generated stylesheet into its base rules and its p3 layer."""
    css = _COMMENT.sub("", render_axis_css(DEFAULT_VALUE_SETS, banner=False))
    marker = "@media (color-gamut: p3) {"
    base_css, _, media_css = css.partition(marker)
    return _declarations(base_css), _declarations(media_css)


def _js_rules() -> tuple[dict, dict]:
    # A file:// URI, not a path: node's ESM loader reads a bare `C:/...` as an
    # unsupported URL scheme.
    script = f"""
    import {{ buildAxisBase }} from {json.dumps(PLUGIN_PATH.as_uri())};
    process.stdout.write(JSON.stringify(buildAxisBase()));
    """
    base = json.loads(_run_node(script))
    media = base.pop("@media (color-gamut: p3)", {})
    return base, media


def test_the_meta_parser_actually_parses():
    """A comparison built on a parser that returns {} would pass vacuously."""
    parsed = _declarations('[data-accent="x"] {\n  --cf-accent: #fff;\n}\n')
    assert parsed == {'[data-accent="x"]': {"--cf-accent": "#fff"}}


@requires_node
def test_the_plugin_and_axes_py_emit_the_same_base_rules():
    python_base, _ = _python_rules()
    js_base, _ = _js_rules()
    assert js_base == python_base


@requires_node
def test_the_plugin_and_axes_py_emit_the_same_p3_layer():
    _, python_media = _python_rules()
    _, js_media = _js_rules()
    assert js_media == python_media


@requires_node
def test_the_parity_check_has_something_to_compare():
    """Guards the two tests above against both sides being empty."""
    python_base, python_media = _python_rules()
    assert len(python_base) > 10, python_base
    assert python_media, "no p3 layer parsed out of the generated stylesheet"


# --- the vendored artifact -------------------------------------------------


def test_the_plugin_ships_inside_the_package():
    assert PLUGIN_PATH.is_file()


def test_the_wheel_ships_the_vendored_artifacts():
    """Vendoring is the distribution decision, so the include glob is load-bearing.

    A consuming app points its Tailwind config at these files inside
    site-packages. Narrowing this glob to, say, ``*.js`` would ship a wheel
    whose documented plugin path does not exist.
    """
    import tomllib

    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = config["tool"]["hatch"]["build"]["include"]
    for artifact in (PLUGIN_PATH, DEFINITION_PATH):
        relative = artifact.relative_to(REPO_ROOT).as_posix()
        assert any(fnmatch(relative, pattern) for pattern in patterns), (
            f"{relative} is not covered by the wheel include patterns {patterns}"
        )


def test_the_plugin_is_dependency_free():
    """Vendored means vendored: no bare imports to resolve in the consumer."""
    source = PLUGIN_PATH.read_text(encoding="utf-8")
    bare = re.findall(r"""^\s*import\s+.*?from\s+["']([^."'][^"']*)["']""", source, re.MULTILINE)
    assert all(name.startswith("node:") for name in bare), (
        f"plugin imports non-builtin modules: {bare}"
    )
