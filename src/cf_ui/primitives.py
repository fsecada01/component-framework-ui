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
    "ALIASES",
    "AXIS_KINDS",
    "CLASSES",
    "CLASS_VALUED",
    "EMPHASIS",
    "LEVELS",
    "PRIMITIVES",
    "PRIMITIVE_DEFINITION_PATH",
    "SIZES",
    "STATES",
    "TYPES",
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

#: Three sizes. Frameworks ship between three and six; three is the
#: intersection that maps cleanly everywhere.
#:
#: ``normal`` is the middle step, *not* "whatever the framework does with no
#: class". Usually those coincide and it maps to an empty string — but Bulma's
#: ``.tag`` defaults to its smallest step, so a normal badge needs
#: ``is-medium`` to line up with a normal button. The shared vocabulary is the
#: point: ``size="normal"`` has to mean one thing across primitives, or
#: sharing it buys nothing.
#:
#: The reverse also happens: Bootstrap and Foundation ship no badge size
#: classes at all, so all three values map to an empty string and ``size`` is
#: inert there. Documented in ``docs/primitives.md`` rather than faked with
#: font-size utilities that cannot reach the right steps.
SIZES: tuple[str, ...] = ("small", "normal", "large")

STATES: tuple[str, ...] = ("normal", "loading", "disabled")

#: Heading levels, as strings — they land in a tag name, and ``{{ level }}``
#: renders ``1`` for both ``1`` and ``"1"``. Kept as strings so the vocabulary
#: and the rendered value are the same type.
LEVELS: tuple[str, ...] = ("1", "2", "3", "4", "5", "6")

#: The three values HTML defines for ``<button type>``.
#:
#: Closed for the same reason every other axis is, but the failure it prevents
#: is worse than an unstyled element: HTML's missing-value default for an
#: *invalid* ``type`` is ``submit``, so ``type="sumbit"`` does not render an
#: inert button — it renders one that submits the enclosing form. cf-ui
#: defaults to ``button`` precisely to avoid that, and an unvalidated typo
#: undoes it silently.
TYPES: tuple[str, ...] = ("button", "submit", "reset")

#: De-emphasis, as an axis rather than a boolean prop.
#:
#: It started as ``subtitle=True`` and had to be promoted: in Bulma ``title``
#: and ``subtitle`` are *alternatives*, not additive, so a boolean outside the
#: map made :func:`classes_for` report ``"title is-4"`` for a call that
#: actually rendered ``subtitle is-4``. A prop that changes which classes are
#: emitted belongs in the map, where the parity test can see it — otherwise it
#: lives on an exception list and the mechanism quietly lies.
#:
#: Bulma is also why ``base`` may be empty: with nothing in ``base``, this
#: axis carries the base class itself, which is how an alternatives-style
#: framework fits a format built for additive ones.
EMPHASIS: tuple[str, ...] = ("normal", "subtle")

VOCABULARIES: dict[str, tuple[str, ...]] = {
    "variant": VARIANTS,
    "size": SIZES,
    "state": STATES,
    "level": LEVELS,
    "emphasis": EMPHASIS,
    "type": TYPES,
}

#: What an axis's value *becomes* in the rendered element.
#:
#: This is not bookkeeping. It answers the two questions the vocabularies on
#: their own cannot, and it answers both from one fact:
#:
#: ``class``
#:     The value is one class among several on an element. It needs a
#:     per-theme entry in :data:`CLASSES`, and an **empty value is benign** —
#:     the class is simply not emitted and the element stays valid, just
#:     unstyled. That matters because Django resolves a missing context
#:     variable to ``""``, so :func:`validate` has to tolerate it.
#:
#: ``tag`` / ``attribute``
#:     The value is the element's name, or an attribute's. There is no class
#:     to map, so :data:`CLASSES` carries no entry — and an **empty value is
#:     not benign**. ``<h{{ level }}>`` with nothing in ``level`` renders
#:     ``<h>``: an element that does not exist, which browsers parse as an
#:     unknown inline. It still picks up the ``title`` class, so it looks
#:     right while being absent from the document outline and unreachable by
#:     screen-reader heading navigation. Silent, and exactly the failure this
#:     module exists to prevent, so :func:`validate` raises instead.
#:
#: ``level`` used to carry a class map of thirty empty strings and a comment
#: warning that a second tag-valued axis would need a real answer. ``type``
#: is that second axis. This is the answer.
AXIS_KINDS: dict[str, str] = {
    "variant": "class",
    "size": "class",
    "state": "class",
    "emphasis": "class",
    "level": "tag",
    "type": "attribute",
}

#: Axes whose value lands in a class — the ones :data:`CLASSES` must map.
CLASS_VALUED: frozenset[str] = frozenset(
    axis for axis, kind in AXIS_KINDS.items() if kind == "class"
)

#: Props whose natural HTML spelling is *not* the name cf-ui uses, mapped to
#: the name that works.
#:
#: These are not typos — they are the spelling a caller will reach for first,
#: and django-cotton accepts an undeclared attribute happily and drops it. The
#: result is valid HTML missing the attribute that mattered:
#: ``<c-cf.label for="email">`` renders a ``<label>`` with no ``for``, so the
#: label is associated with nothing and no error says so.
#:
#: ``for`` is renamed because it is a Python reserved word and JinjaX cannot
#: express it as a prop. Each wrapper forwards the HTML spelling into
#: :func:`validate`, which raises here rather than letting it vanish.
#:
#: This traps *declared* aliases only. An arbitrary misspelling
#: (``<c-cf.icon labl="…">``) is still dropped silently, by django-cotton, for
#: every cotton component in every project — not something cf-ui can close
#: from inside a wrapper. See ``docs/primitives.md``.
ALIASES: dict[str, dict[str, str]] = {
    "label": {"for": "for_id"},
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
    "button": ("variant", "size", "state", "type"),
    "badge": ("variant", "size"),
    "heading": ("level", "size", "emphasis"),
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

_BADGE_CLASSES: dict[str, dict[str, Any]] = {
    "bulma": {
        "base": "tag",
        "variant": {
            "primary": "is-primary",
            "secondary": "is-link",
            "success": "is-success",
            "warning": "is-warning",
            "danger": "is-danger",
            "info": "is-info",
            "neutral": "",
        },
        # The one place `normal` is not an empty class. Bulma's `.tag` defaults
        # to its *smallest* step (0.75rem — a button's `is-small`), so reaching
        # the middle step needs `is-medium`. See the note on SIZES.
        "size": {"small": "", "normal": "is-medium", "large": "is-large"},
    },
    "bootstrap": {
        "base": "badge",
        "variant": {
            "primary": "text-bg-primary",
            "secondary": "text-bg-secondary",
            "success": "text-bg-success",
            "warning": "text-bg-warning",
            "danger": "text-bg-danger",
            # Not "": a `.badge` with no colour class is #fff on a transparent
            # background — invisible. `neutral` cannot be the default here.
            "neutral": "text-bg-light",
            "info": "text-bg-info",
        },
        # Bootstrap 5.3 ships no badge size modifiers; badges scale from the
        # parent via `$badge-font-size: .75em`. Not faked with `fs-*`, whose
        # scale bottoms out *larger* than a default badge and so cannot express
        # "small" at all.
        "size": {"small": "", "normal": "", "large": ""},
    },
    "foundation": {
        "base": "label",
        "variant": {
            "primary": "primary",
            "secondary": "secondary",
            "success": "success",
            "warning": "warning",
            "danger": "alert",
            # Foundation labels ship five colours and no informational one.
            "info": "secondary",
            "neutral": "",
        },
        # Foundation ships no label size classes at all — one font-size, no
        # modifiers. `size` is inert on this theme.
        "size": {"small": "", "normal": "", "large": ""},
    },
    "fomantic": {
        "base": "ui label",
        "variant": {
            "primary": "primary",
            "secondary": "secondary",
            # `green`/`red`, not the button map's `positive`/`negative`:
            # `.ui.positive.label` and `.ui.negative.label` do not exist in
            # Fomantic 2.9.3 — those are button and message variations.
            "success": "green",
            "warning": "yellow",
            "danger": "red",
            "info": "teal",
            "neutral": "",
        },
        "size": {"small": "small", "normal": "", "large": "large"},
    },
    "daisy": {
        "base": "badge",
        "variant": {
            "primary": "badge-primary",
            "secondary": "badge-secondary",
            "success": "badge-success",
            "warning": "badge-warning",
            "danger": "badge-error",
            "info": "badge-info",
            "neutral": "badge-neutral",
        },
        "size": {"small": "badge-sm", "normal": "", "large": "badge-lg"},
    },
}

_HEADING_CLASSES: dict[str, dict[str, Any]] = {
    "bulma": {
        # Empty, because `title` and `subtitle` are alternatives rather than
        # additive — the emphasis axis carries the base class instead. This is
        # the case that forced `emphasis` to become an axis at all.
        "base": "",
        "size": {"small": "is-6", "normal": "is-4", "large": "is-2"},
        "emphasis": {"normal": "title", "subtle": "subtitle"},
    },
    "bootstrap": {
        "base": "",
        # `.h1`–`.h6` are real utilities that outrank the tag selector, which
        # is what lets level and size be set independently.
        "size": {"small": "h6", "normal": "h4", "large": "h1"},
        "emphasis": {"normal": "", "subtle": "text-body-secondary"},
    },
    "foundation": {
        "base": "",
        "size": {"small": "h6", "normal": "h4", "large": "h2"},
        "emphasis": {"normal": "", "subtle": "subheader"},
    },
    "fomantic": {
        "base": "ui header",
        # Fomantic's ladder is mini/tiny/small/(nothing)/large/big/huge/massive
        # — there is no `.ui.medium.header`. `normal` therefore emits the
        # literal token `large`. It reads oddly, and it is the only way to keep
        # three distinct steps while always emitting a size class; omitting one
        # for `normal` would re-couple size to the tag.
        "size": {"small": "small", "normal": "large", "large": "massive"},
        # `grey`, not the idiomatic `.ui.sub.header`: `sub` sets a font-size
        # *after* every size variation at equal specificity, so it silently
        # destroys the size axis. Colour-only is the compatible choice.
        "emphasis": {"normal": "", "subtle": "grey"},
    },
    "daisy": {
        # Tailwind Preflight strips font-size and font-weight from h1–h6, so
        # without this a daisy heading renders as body text.
        "base": "font-bold",
        "size": {"small": "text-base", "normal": "text-2xl", "large": "text-4xl"},
        "emphasis": {"normal": "", "subtle": "opacity-60"},
    },
}

_LABEL_CLASSES: dict[str, dict[str, Any]] = {
    "bulma": {
        "base": "label",
        "size": {"small": "is-small", "normal": "", "large": "is-large"},
    },
    "bootstrap": {
        "base": "form-label",
        # No `form-label-sm`/`-lg` exists. `.small` (.875em) and `.fs-5`
        # (1.25rem) are the exact sizes Bootstrap's own `.col-form-label-sm`
        # and `-lg` use, so the scale is Bootstrap's rather than invented.
        "size": {"small": "small", "normal": "", "large": "fs-5"},
    },
    "foundation": {
        # Empty deliberately. Foundation styles `<label>` by element, and its
        # `.label` class is the *badge* component — applying it would turn
        # every field label into a blue pill.
        "base": "",
        # Foundation ships no font-size scale outside the button scale, so
        # `small` has nothing to map to. `large` collapses onto `.lead`
        # (125%, the size `.button.large` uses).
        "size": {"small": "", "normal": "", "large": "lead"},
    },
    "fomantic": {
        # Empty: the only rule is `.ui.form .field > label`, so the label is
        # styled by ancestry. `.ui.label` is again the badge element.
        "base": "",
        # These land on the `.ui.form` ancestor, not the label — see the note
        # on classes_for() about multi-element primitives.
        "size": {"small": "small", "normal": "", "large": "large"},
    },
    "daisy": {
        "base": "label",
        # These land on the inner `.label-text` span: `.label-text` sets its
        # own font-size, so a utility on the outer label is overridden rather
        # than inherited.
        "size": {"small": "text-xs", "normal": "", "large": "text-lg"},
    },
}

_ICON_CLASSES: dict[str, dict[str, Any]] = {
    "bulma": {
        # The one theme with a real icon element: `.icon` does the flex
        # centring and fixed 1.5rem box that hand-written markup misses.
        "base": "icon",
        "size": {"small": "is-small", "normal": "", "large": "is-large"},
    },
    "bootstrap": {
        # Bootstrap ships no icon wrapper class.
        "base": "",
        # A mixed scale, honestly: `.small` is em-relative (.875em) and
        # composes inside a `btn-sm`, but Bootstrap has no em-relative large,
        # so `.fs-4` is absolute and does not. The alternatives (`.h4`,
        # `.lead`, `.display-6`) all carry margin or weight and are worse.
        "size": {"small": "small", "normal": "", "large": "fs-4"},
    },
    "foundation": {
        # Foundation has no icon wrapper and no font-size utility scale. Its
        # `.small-*` classes are grid breakpoint columns and would be actively
        # harmful here, so `size` is entirely inert on this theme — the
        # component earns its place through the aria decision alone.
        "base": "",
        "size": {"small": "", "normal": "", "large": ""},
    },
    "fomantic": {
        # `.ui.icon` standalone does not exist — Fomantic's icon rules are
        # element-qualified (`i.icon`), so a <span> wrapper gets nothing from
        # them. `span.ui.text` is qualified to exactly this element and its
        # small/large steps are the *same* font sizes as `i.small.icon` and
        # `i.large.icon`, so this reproduces the native icon scale.
        "base": "ui text",
        "size": {"small": "small", "normal": "", "large": "large"},
    },
    "daisy": {
        "base": "inline-flex items-center justify-center",
        # Arbitrary em values rather than `text-sm`/`text-2xl`: Tailwind's
        # `text-*` scale is rem-absolute, so a `text-2xl` icon inside a
        # `btn-sm` would not scale with its container. No fixed box either — it
        # would fight the large font-size.
        "size": {"small": "text-[0.75em]", "normal": "", "large": "text-[1.5em]"},
    },
}

#: Per-component maps, each keyed by theme. Adding a primitive is one entry
#: here plus its templates — the assembly below and every test derive from it.
_COMPONENT_CLASSES: dict[str, dict[str, dict[str, Any]]] = {
    "button": _BUTTON_CLASSES,
    "badge": _BADGE_CLASSES,
    "heading": _HEADING_CLASSES,
    "label": _LABEL_CLASSES,
    "icon": _ICON_CLASSES,
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

    An **empty** value is where this gets subtle, and :data:`AXIS_KINDS` is
    what decides it. Django resolves a missing context variable to ``""``, so
    an empty class-valued axis has to pass — it drops a class and leaves a
    valid element. An empty tag- or attribute-valued axis does not: it renders
    ``<h>`` or ``type=""``, which is malformed rather than merely unstyled, so
    it raises.

    Args:
        component: A key of :data:`PRIMITIVES`.
        **axes: Axis values to check, e.g. ``variant="primary"``. May also
            carry a declared alias from :data:`ALIASES` — a wrapper forwards
            the HTML spelling so it can be rejected rather than dropped.

    Returns:
        The empty string, always.

    Raises:
        PrimitiveConfigError: On an unknown component, an axis the component
            does not accept, a value outside that axis's vocabulary, an empty
            value for an axis that cannot take one, or a declared alias.
    """
    accepted = PRIMITIVES.get(component)
    if accepted is None:
        known = ", ".join(sorted(PRIMITIVES))
        raise PrimitiveConfigError(f"unknown primitive {component!r} — known primitives: {known}")

    aliases = ALIASES.get(component, {})

    for axis, value in axes.items():
        if value is None or value == "":
            # Benign for a class — the class is not emitted and the element
            # stays valid. Not benign for a tag or an attribute.
            kind = AXIS_KINDS.get(axis)
            if axis in accepted and kind is not None and kind != "class":
                raise PrimitiveConfigError(
                    f"{component} needs a {axis} — it becomes the element's "
                    f"{kind}, so an empty one renders malformed markup rather "
                    f"than unstyled markup. Pass one of: "
                    f"{', '.join(VOCABULARIES[axis])}"
                )
            continue
        if axis in aliases:
            raise PrimitiveConfigError(
                f"{component} takes no {axis!r} — use {aliases[axis]!r}. "
                f"({axis!r} is a Python reserved word, so the prop is spelled "
                f"differently; passing the HTML name would silently drop it.)"
            )
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

    **Lossy for multi-element primitives.** The return value is a flat string,
    which assumes every class in the map belongs on one element. Two shipped
    primitives break that assumption: Fomantic styles a label through
    ``.ui.form .field > label`` ancestry, and daisyUI puts a label's size on an
    inner ``.label-text`` span. So ``classes_for("daisy", "label",
    size="large")`` returns ``"label text-lg"`` — a union of two elements'
    classes, not a string to paste on either one. The templates are the
    authority on placement; this function is the authority on membership, and
    the parity test in ``tests/unit/test_primitives.py`` compares the two as
    token *sets* for exactly that reason.
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
        if axis not in CLASS_VALUED:
            continue  # tag- and attribute-valued axes carry no class
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
        "axis_kinds": dict(AXIS_KINDS),
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
