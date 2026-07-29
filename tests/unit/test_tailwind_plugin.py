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
from copy import deepcopy
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
    #
    # `validate: false` is passed deliberately. buildAxisBase validates by
    # default since #20, and comparing only *validated* input would quietly
    # narrow this from "the two generators agree" to "they agree on input the
    # validator already approved" — the unchecked generation path is exactly
    # the one a consumer reaches through the exported function.
    script = f"""
    import {{ buildAxisBase }} from {json.dumps(PLUGIN_PATH.as_uri())};
    process.stdout.write(
      JSON.stringify(buildAxisBase(undefined, undefined, {{ validate: false }})),
    );
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


# --- cross-language validation parity (issue #20) ---------------------------
#
# #20 §1 closed an asymmetry: the JS generator rejected unsafe token values and
# the Python one did not. These assert the two now reject the *same* inputs,
# which is the property that keeps them from drifting apart again.

UNSAFE = [
    "0; } body { display: none",
    "red; color: blue",
    "}",
    "{",
    "red /* c",
    "red */",
    "</style><script>alert(1)</script>",
    "<",
]
SAFE = ["0", "0.375rem", "none", "0 1px 2px rgb(0 0 0 / 0.08)", "#ffffff"]


def _python_rejects(value: str) -> bool:
    from cf_ui.axes import AxisConfigError, merge_value_sets

    try:
        merge_value_sets({"form": {"probe": {"--cf-radius": value}}})
    except AxisConfigError:
        return True
    return False


def _js_rejects(values: list[str]) -> list[bool]:
    """One node process for the whole batch — spawning eight is needlessly slow."""
    script = f"""
    import {{ mergeValueSets, loadDefinition }} from {json.dumps(PLUGIN_PATH.as_uri())};
    const definition = loadDefinition();
    const results = {json.dumps(values)}.map((value) => {{
      try {{
        mergeValueSets(definition, {{ form: {{ probe: {{ "--cf-radius": value }} }} }});
        return false;
      }} catch {{
        return true;
      }}
    }});
    process.stdout.write(JSON.stringify(results));
    """
    return json.loads(_run_node(script))


@requires_node
def test_both_generators_reject_the_same_unsafe_values():
    js = _js_rejects(UNSAFE)
    python = [_python_rejects(value) for value in UNSAFE]
    assert python == [True] * len(UNSAFE), f"python accepted: {UNSAFE}"
    assert js == python, dict(zip(UNSAFE, zip(python, js, strict=True), strict=True))


@requires_node
def test_both_generators_accept_the_same_legitimate_values():
    """Guards the test above against a rule that simply rejects everything."""
    js = _js_rejects(SAFE)
    python = [_python_rejects(value) for value in SAFE]
    assert python == [False] * len(SAFE), f"python rejected a legal value: {SAFE}"
    assert js == python, dict(zip(SAFE, zip(python, js, strict=True), strict=True))


@requires_node
def test_both_generators_report_the_same_p3_lightness_failures():
    """#20 §3 — the invariant is checked on both sides, in the same words."""
    from cf_ui.axes import DEFAULT_VALUE_SETS, p3_lightness_failures

    script = f"""
    import {{ p3LightnessFailures, loadDefinition }} from {json.dumps(PLUGIN_PATH.as_uri())};
    const definition = loadDefinition();
    const drifted = structuredClone(definition.valueSets);
    drifted.accent.azure.p3.light["--cf-accent"] = "oklch(72.0% 0.137 242.7)";
    process.stdout.write(JSON.stringify({{
      clean: p3LightnessFailures(definition.valueSets, definition),
      drifted: p3LightnessFailures(drifted, definition),
    }}));
    """
    js = json.loads(_run_node(script))

    drifted = deepcopy(DEFAULT_VALUE_SETS)
    drifted["accent"]["azure"]["p3"]["light"]["--cf-accent"] = "oklch(72.0% 0.137 242.7)"

    assert js["clean"] == p3_lightness_failures(DEFAULT_VALUE_SETS) == []
    assert js["drifted"] == p3_lightness_failures(drifted)
    assert js["drifted"], "the drifted fixture must actually fail, or this is vacuous"


# --- generated artifacts stay clean ----------------------------------------


def test_generated_artifacts_are_pinned_to_lf():
    """`python -m cf_ui.axes` writes LF; without this git shows a phantom diff.

    The generator writes ``newline="\\n"`` while git's autocrlf wants CRLF, so
    regenerating left the tree permanently "modified" with a zero-line diff —
    which makes "is the tree clean" useless as a signal for every phase that
    touches these files.
    """
    attributes = REPO_ROOT / ".gitattributes"
    assert attributes.is_file(), "a .gitattributes is needed to pin the generated artifacts"
    text = attributes.read_text(encoding="utf-8")
    for name in ("cf_ui_axes.css", "cf_ui_axes.json"):
        assert name in text, f"{name} is not pinned in .gitattributes"
    assert "text eol=lf" in text


def test_regenerating_the_artifacts_is_a_no_op():
    """The checked-in artifacts match what the generator produces, byte for byte."""
    import json as _json

    from cf_ui.axes import (
        AXIS_CSS_PATH,
        AXIS_DEFINITION_PATH,
        DEFAULT_VALUE_SETS,
        axis_definition,
        render_axis_css,
    )

    assert AXIS_CSS_PATH.read_text(encoding="utf-8") == render_axis_css(DEFAULT_VALUE_SETS)
    expected = _json.dumps(axis_definition(), indent=2) + "\n"
    assert AXIS_DEFINITION_PATH.read_text(encoding="utf-8") == expected
