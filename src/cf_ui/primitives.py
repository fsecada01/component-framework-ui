"""Primitive vocabularies — the closed sets behind ``variant``/``size``/``state``.

:mod:`cf_ui.axes` answers *what does this app look like*. This module answers
the narrower question the primitives ask: *which of a fixed set of roles does
this button play*. Same discipline, same reason — an open-ended ``variant``
string produces a different button in every consumer, and the closed set is
what makes "primary" mean one thing across five CSS frameworks.

Why the classes live here **and** in the templates
--------------------------------------------------

They are duplicated on purpose, and the duplication is guarded.

daisyUI compiles through Tailwind, whose scanner reads source *text*. A
template that writes ``btn-{{ variant }}`` hands Tailwind nothing to find, so
every variant class is removed from the build — silently, with an unstyled
page as the only symptom (``docs/daisyui.md``). Emitting the class from Python
has exactly the same effect. So the templates must spell every class out
literally, in full, one ``{% if %}`` branch per value.

That would normally mean the real vocabulary lives in ten template files and
nothing states it. Hence this module: it is the reviewable source of truth,
the input to ``cf_ui_primitives.json`` that the Tailwind plugin safelists from,
and the thing ``tests/unit/test_primitives.py`` holds the templates against in
both directions. Neither copy is allowed to move alone.

Why :func:`validate` exists
---------------------------

A literal ``{% if %}`` chain has no ``else``. Handed ``variant="purple"`` it
emits nothing at all and renders an unstyled element — not an error, not a
warning, just a button that looks wrong. Every primitive template therefore
calls :func:`validate` once, in a position that renders its (empty) result, so
a bad prop raises where it was passed instead of surfacing as a visual bug
three screens away.

Regenerate the JSON with::

    python -m cf_ui.primitives
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from cf_ui.themes import THEMES

__all__ = [
    "CLASSES",
    "LEVELS",
    "PRIMITIVES",
    "PRIMITIVE_DEFINITION_PATH",
    "SIZES",
    "STATES",
    "VARIANTS",
    "VOCABULARIES",
    "PrimitiveConfigError",
    "classes_for",
    "primitive_definition",
    "validate",
]


class PrimitiveConfigError(ValueError):
    """Raised for an unknown primitive, axis, or axis value."""


# ---------------------------------------------------------------------------
# Vocabularies
#
# Seven variants, not "whatever the framework ships". Every one of the five
# frameworks can express all seven, though two of them collapse a pair onto
# the same class — see the notes in CLASSES. A vocabulary sized to the poorest
# framework would make the richer ones useless; one sized to the richest would
# make "info" mean nothing in Foundation.
# ---------------------------------------------------------------------------

VARIANTS: tuple[str, ...] = (
    "primary",
    "secondary",
    "success",
    "warning",
    "danger",
    "info",
    "neutral",
)

#: Three sizes. Frameworks ship between three and six; three is the intersection
#: that maps cleanly everywhere, and "normal" is always the framework default
#: (an empty class) rather than an explicit token.
SIZES: tuple[str, ...] = ("small", "normal", "large")

STATES: tuple[str, ...] = ("normal", "loading", "disabled")

#: Heading levels, as strings — they land in a tag name, and ``{{ level }}``
#: renders ``1`` for both ``1`` and ``"1"``. Kept as strings so the vocabulary
#: and the rendered value are the same type.
LEVELS: tuple[str, ...] = ("1", "2", "3", "4", "5", "6")

VOCABULARIES: dict[str, tuple[str, ...]] = {
    "variant": VARIANTS,
    "size": SIZES,
    "state": STATES,
    "level": LEVELS,
}

#: Which axes each primitive accepts. This is the prop contract for all of
#: Tier 1, settled as a set (#52) — ``docs/primitives.md`` is the prose
#: version. Only components listed in :data:`cf_ui.themes.COMPONENTS` have
#: templates; the rest are contract-only until their phase lands.
#:
#: ``label`` and ``icon`` deliberately take no ``variant``: a label's colour
#: belongs to the field it labels, and an icon's belongs to whatever contains
#: it. Giving them one invites two sources of truth for the same colour.
PRIMITIVES: dict[str, tuple[str, ...]] = {
    "button": ("variant", "size", "state"),
    "badge": ("variant", "size"),
    "heading": ("level", "size"),
    "label": ("size",),
    "icon": ("size",),
}


# ---------------------------------------------------------------------------
# Per-theme classes
#
# An empty string means "the framework's default needs no class" — it is a
# real, deliberate entry, not a gap. The completeness test treats a *missing*
# key as the failure, so the distinction is enforced rather than assumed.
# ---------------------------------------------------------------------------

_BUTTON_CLASSES: dict[str, dict[str, Any]] = {
    "bulma": {
        "base": "button",
        "variant": {
            "primary": "is-primary",
            "secondary": "is-link",
            "success": "is-success",
            "warning": "is-warning",
            "danger": "is-danger",
            "info": "is-info",
            "neutral": "",
        },
        "size": {"small": "is-small", "normal": "", "large": "is-large"},
        # Bulma styles disabled off the attribute, not a class.
        "state": {"normal": "", "loading": "is-loading", "disabled": ""},
    },
    "bootstrap": {
        "base": "btn",
        "variant": {
            "primary": "btn-primary",
            "secondary": "btn-secondary",
            "success": "btn-success",
            "warning": "btn-warning",
            "danger": "btn-danger",
            "info": "btn-info",
            "neutral": "btn-light",
        },
        "size": {"small": "btn-sm", "normal": "", "large": "btn-lg"},
        # Bootstrap has no loading class — the spinner is an element.
        # `.disabled` is what makes a disabled <a> look disabled.
        "state": {"normal": "", "loading": "", "disabled": "disabled"},
    },
    "foundation": {
        "base": "button",
        "variant": {
            "primary": "primary",
            "secondary": "secondary",
            "success": "success",
            "warning": "warning",
            "danger": "alert",
            # Foundation ships five button colours and no informational one.
            # `info` collapses onto secondary rather than inventing a class
            # the framework's own CSS does not define.
            "info": "secondary",
            "neutral": "",
        },
        "size": {"small": "small", "normal": "", "large": "large"},
        "state": {"normal": "", "loading": "", "disabled": "disabled"},
    },
    "fomantic": {
        "base": "ui button",
        "variant": {
            "primary": "primary",
            "secondary": "secondary",
            "success": "positive",
            "warning": "yellow",
            "danger": "negative",
            "info": "teal",
            "neutral": "",
        },
        "size": {"small": "small", "normal": "", "large": "large"},
        "state": {"normal": "", "loading": "loading", "disabled": "disabled"},
    },
    "daisy": {
        "base": "btn",
        "variant": {
            "primary": "btn-primary",
            "secondary": "btn-secondary",
            "success": "btn-success",
            "warning": "btn-warning",
            "danger": "btn-error",
            "info": "btn-info",
            "neutral": "btn-neutral",
        },
        "size": {"small": "btn-sm", "normal": "", "large": "btn-lg"},
        # daisyUI's loading indicator is an element (`<span class="loading">`),
        # so `loading` carries no button class of its own.
        "state": {"normal": "", "loading": "", "disabled": "btn-disabled"},
    },
}

#: Per-component maps, each keyed by theme. Adding a primitive is one entry
#: here plus its templates — the assembly below and every test derive from it.
_COMPONENT_CLASSES: dict[str, dict[str, dict[str, Any]]] = {
    "button": _BUTTON_CLASSES,
}


def _assemble() -> dict[str, dict[str, dict[str, Any]]]:
    """Invert ``{component: {theme: ...}}`` into ``{theme: {component: ...}}``.

    Authored per component because that is the unit of work; consumed per
    theme because that is the unit of rendering. A component missing a theme
    is caught here rather than at render time.
    """
    assembled: dict[str, dict[str, dict[str, Any]]] = {theme: {} for theme in THEMES}
    for component, by_theme in _COMPONENT_CLASSES.items():
        missing = set(THEMES) - set(by_theme)
        if missing:
            raise PrimitiveConfigError(
                f"{component} has no class map for {sorted(missing)} — every primitive "
                "must cover every theme in cf_ui.themes.THEMES"
            )
        for theme in THEMES:
            assembled[theme][component] = deepcopy(by_theme[theme])
    return assembled


#: ``{theme: {component: {axis: {value: classes}}}}``.
CLASSES: dict[str, dict[str, dict[str, Any]]] = _assemble()


# ---------------------------------------------------------------------------
# The guard
# ---------------------------------------------------------------------------


def validate(component: str, **axes: Any) -> str:
    """Reject an unknown primitive, axis, or axis value.

    Called from every primitive template — as a Jinja global and as the
    ``{% cf_ui_validate %}`` Django tag — in a position that renders the
    result, hence the empty-string return.

    Only the axes actually passed are checked. Templates forward whatever
    they were given, and an omitted prop is filled by the component's default
    further down, so absence is not an error.

    Args:
        component: A key of :data:`PRIMITIVES`.
        **axes: Axis values to check, e.g. ``variant="primary"``.

    Returns:
        The empty string, always.

    Raises:
        PrimitiveConfigError: On an unknown component, an axis the component
            does not accept, or a value outside that axis's vocabulary.
    """
    accepted = PRIMITIVES.get(component)
    if accepted is None:
        known = ", ".join(sorted(PRIMITIVES))
        raise PrimitiveConfigError(f"unknown primitive {component!r} — known primitives: {known}")

    for axis, value in axes.items():
        if value is None or value == "":
            continue
        if axis not in accepted:
            raise PrimitiveConfigError(
                f"{component} takes no {axis!r} — it accepts: {', '.join(accepted)}"
            )
        allowed = VOCABULARIES[axis]
        if str(value) not in allowed:
            raise PrimitiveConfigError(
                f"invalid {axis} {value!r} for {component} — {axis} must be one of: "
                f"{', '.join(allowed)}"
            )
    return ""


def build_primitive_globals() -> dict[str, Any]:
    """Jinja globals the primitive templates call.

    Bound by both installers, alongside the axis globals. A primitive rendered
    without them raises ``'cf_ui_validate' is undefined`` — loud, and naming
    the missing piece, which is the same trade ``cf_ui_root_attrs()`` already
    makes.
    """
    return {"cf_ui_validate": validate}


def classes_for(theme: str, component: str, **axes: Any) -> str:
    """The class string a primitive resolves to, validated.

    **Not used by the templates**, and deliberately so — a class computed at
    render time is invisible to Tailwind's scanner and gets tree-shaken out of
    a daisyUI build. It exists for tests, documentation, and consumers
    rendering outside the shipped templates entirely.
    """
    validate(component, **axes)
    try:
        mapping = CLASSES[theme][component]
    except KeyError as exc:
        raise PrimitiveConfigError(
            f"no class map for {theme}/{component} — implemented primitives per theme: "
            f"{', '.join(sorted(CLASSES.get(theme, {})))}"
        ) from exc

    parts = [mapping["base"]]
    for axis in PRIMITIVES[component]:
        value = axes.get(axis)
        if value:
            parts.append(mapping[axis][str(value)])
    return " ".join(part for part in parts if part)


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

PRIMITIVE_DEFINITION_PATH = Path(__file__).parent / "static" / "cf_ui" / "cf_ui_primitives.json"


def primitive_definition() -> dict[str, Any]:
    """Export the vocabularies and class maps as JSON-serializable data.

    Read by ``cf_ui_tailwind_plugin.mjs`` so a daisyUI build can safelist every
    primitive class without a second copy of the value sets in JavaScript —
    the same arrangement :func:`cf_ui.axes.axis_definition` has.

    Returns:
        A deep copy — callers may mutate the result freely.
    """
    return {
        "vocabularies": {axis: list(values) for axis, values in VOCABULARIES.items()},
        "primitives": {name: list(axes) for name, axes in PRIMITIVES.items()},
        "classes": deepcopy(CLASSES),
    }


def _regenerate() -> list[Path]:
    PRIMITIVE_DEFINITION_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRIMITIVE_DEFINITION_PATH.write_text(
        json.dumps(primitive_definition(), indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return [PRIMITIVE_DEFINITION_PATH]


if __name__ == "__main__":  # pragma: no cover
    for path in _regenerate():
        print(f"wrote {path}")
