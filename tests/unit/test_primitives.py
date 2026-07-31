"""The primitives vocabulary is a closed set, and the templates agree with it (#52).

Three things are guarded here, and the third is the one that matters.

**Closed sets.** ``variant``/``size``/``state``/``level`` are fixed vocabularies,
validated the way :mod:`cf_ui.axes` validates axis value names — an unknown
value raises rather than being passed through.

**Loudness.** A literal ``{% if variant == 'primary' %}`` chain emits *nothing*
for a value it does not recognise. Unstyled markup is not an error anyone
notices, so every primitive template calls the guard once and a bad prop
raises there.

**Parity.** The classes cannot be emitted from Python: daisyUI compiles through
Tailwind, whose scanner reads source *text*, so a computed class name is
tree-shaken out silently (see ``docs/daisyui.md``). The templates must
therefore spell every class literally — which means two copies of the same
knowledge, one in ``primitives.py`` and one in 10 template files. The parity
test below is what stops them diverging; without it this module would be
decoration.
"""

import re
from pathlib import Path

import pytest

from cf_ui.primitives import (
    CLASSES,
    EMPHASIS,
    LEVELS,
    PRIMITIVES,
    SIZES,
    STATES,
    VARIANTS,
    VOCABULARIES,
    PrimitiveConfigError,
    primitive_definition,
    validate,
)
from cf_ui.themes import COMPONENTS, THEMES

REPO_ROOT = Path(__file__).parent.parent.parent
JINJA_DIR = REPO_ROOT / "src" / "cf_ui" / "templates" / "jinja"
COTTON_THEME_DIR = REPO_ROOT / "src" / "cf_ui" / "templates" / "cotton" / "_themes"

#: Components whose per-theme class maps ship in this phase. The prop contract
#: is settled for all of Tier 1 (see ``docs/primitives.md``); the class maps
#: land with each component's templates.
IMPLEMENTED = ("badge", "button", "heading", "icon", "label")


# ── The vocabularies are closed ───────────────────────────────────────────


def test_the_vocabularies_are_registered_under_their_axis_names():
    assert VOCABULARIES == {
        "variant": VARIANTS,
        "size": SIZES,
        "state": STATES,
        "level": LEVELS,
        "emphasis": EMPHASIS,
    }


@pytest.mark.parametrize("axis", sorted(VOCABULARIES))
def test_no_vocabulary_is_empty(axis: str):
    """A vocabulary that silently emptied would make every value invalid."""
    assert VOCABULARIES[axis], f"{axis} has no values — validate() would reject everything"


@pytest.mark.parametrize("component", sorted(PRIMITIVES))
def test_every_primitive_declares_axes_that_exist(component: str):
    unknown = set(PRIMITIVES[component]) - set(VOCABULARIES)
    assert not unknown, f"{component} declares axes with no vocabulary: {sorted(unknown)}"


@pytest.mark.parametrize("component", IMPLEMENTED)
def test_every_implemented_primitive_is_a_registered_cotton_component(component: str):
    """``cotton_partial`` rejects anything not in ``themes.COMPONENTS``.

    Registering the name there is what makes ``<c-cf.button>`` resolvable at
    all, so a primitive missing from that tuple is inert. Only *implemented*
    primitives belong there — registering a name whose partial does not exist
    turns a clear ``ThemeError`` into a ``TemplateDoesNotExist`` at first
    render, which is strictly worse.
    """
    assert component in COMPONENTS


@pytest.mark.parametrize("component", sorted(set(PRIMITIVES) - set(IMPLEMENTED)))
def test_a_contract_only_primitive_is_not_registered_yet(component: str):
    """The other half: nothing is registered before its templates exist."""
    assert component not in COMPONENTS, (
        f"{component} is registered in themes.COMPONENTS but has no partials — "
        "add it to IMPLEMENTED once its templates land"
    )


# ── A bad value raises, rather than rendering unstyled ────────────────────


def test_validate_accepts_every_declared_value():
    for component, axes in PRIMITIVES.items():
        for axis in axes:
            for value in VOCABULARIES[axis]:
                assert validate(component, **{axis: value}) == ""


def test_validate_returns_empty_string_so_a_template_can_call_it():
    """It is invoked for its exception, in a position that renders its result."""
    assert validate("button", variant="primary") == ""


@pytest.mark.parametrize(
    ("component", "axes", "expected_fragment"),
    [
        ("button", {"variant": "purple"}, "purple"),
        ("button", {"size": "enormous"}, "enormous"),
        ("button", {"state": "hovering"}, "hovering"),
        ("heading", {"level": "7"}, "7"),
        ("heading", {"level": 7}, "7"),
    ],
    ids=lambda v: str(v)[:40],
)
def test_an_unknown_value_raises(component: str, axes: dict, expected_fragment: str):
    with pytest.raises(PrimitiveConfigError) as excinfo:
        validate(component, **axes)
    assert expected_fragment in str(excinfo.value)


def test_the_error_names_the_values_that_would_have_worked():
    """A rejection that does not say what to use instead just moves the guess."""
    with pytest.raises(PrimitiveConfigError) as excinfo:
        validate("button", variant="purple")
    message = str(excinfo.value)
    for value in VARIANTS:
        assert value in message


def test_an_unknown_component_raises():
    with pytest.raises(PrimitiveConfigError, match="widget"):
        validate("widget", variant="primary")


def test_an_axis_the_component_does_not_take_raises():
    """``label`` has no variant. Accepting one silently would render nothing."""
    assert "variant" not in PRIMITIVES["label"]
    with pytest.raises(PrimitiveConfigError, match="variant"):
        validate("label", variant="primary")


def test_an_omitted_axis_is_not_validated():
    """Templates pass only what they were given; a default fills in downstream."""
    assert validate("button") == ""


# ── Every theme covers every value ────────────────────────────────────────


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("component", IMPLEMENTED)
def test_every_theme_maps_every_value_of_every_axis(theme: str, component: str):
    """A missing key is an unstyled variant, which review does not catch."""
    mapping = CLASSES[theme][component]
    for axis in PRIMITIVES[component]:
        missing = set(VOCABULARIES[axis]) - set(mapping.get(axis, {}))
        assert not missing, f"{theme}/{component} has no {axis} class for {sorted(missing)}"


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("component", IMPLEMENTED)
def test_no_theme_maps_a_value_outside_the_vocabulary(theme: str, component: str):
    mapping = CLASSES[theme][component]
    for axis, values in mapping.items():
        if axis == "base":  # a bare class string, not an axis
            continue
        assert axis in VOCABULARIES, f"{theme}/{component} maps a non-axis key {axis!r}"
        extra = set(values) - set(VOCABULARIES[axis])
        assert not extra, f"{theme}/{component} maps unknown {axis} values {sorted(extra)}"


@pytest.mark.parametrize("theme", THEMES)
def test_every_theme_has_a_base_class_entry(theme: str):
    for component in IMPLEMENTED:
        assert "base" in CLASSES[theme][component]


# ── Templates and the map agree ───────────────────────────────────────────


def _literal_classes(text: str) -> set[str]:
    """Every class token spelled literally in a ``class="..."`` attribute.

    Deliberately naive: it reads source text, which is exactly what Tailwind's
    scanner does. Jinja/Django expressions inside the attribute are dropped, so
    what is left is what survives tree-shaking.
    """
    tokens: set[str] = set()
    for attr in re.findall(r'class="([^"]*)"', text):
        attr = re.sub(r"\{\{.*?\}\}|\{%.*?%\}", " ", attr, flags=re.S)
        tokens.update(t for t in attr.split() if t)
    return tokens


def _mapped_classes(theme: str, component: str) -> set[str]:
    tokens: set[str] = set()
    for axis, values in CLASSES[theme][component].items():
        entries = [values] if axis == "base" else list(values.values())
        for entry in entries:
            tokens.update(str(entry).split())
    return tokens


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("component", IMPLEMENTED)
def test_the_jinja_template_spells_every_mapped_class_literally(theme: str, component: str):
    """The Tailwind constraint, enforced.

    ``docs/daisyui.md``: a computed class name is removed from the build with
    no error and an unstyled page as the only symptom. So every class in the
    map has to appear as source text.
    """
    path = JINJA_DIR / theme / f"{component.title()}.jinja"
    missing = _mapped_classes(theme, component) - _literal_classes(path.read_text(encoding="utf-8"))
    assert not missing, (
        f"{path.relative_to(REPO_ROOT)} never spells {sorted(missing)} literally — "
        "Tailwind's scanner reads source text, so these would be tree-shaken away"
    )


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("component", IMPLEMENTED)
def test_the_cotton_partial_spells_every_mapped_class_literally(theme: str, component: str):
    path = COTTON_THEME_DIR / theme / f"{component}.html"
    missing = _mapped_classes(theme, component) - _literal_classes(path.read_text(encoding="utf-8"))
    assert not missing, f"{path.relative_to(REPO_ROOT)} never spells {sorted(missing)} literally"


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("component", IMPLEMENTED)
def test_the_templates_introduce_no_class_the_map_does_not_know(theme: str, component: str):
    """The other direction — otherwise the map documents a subset of reality.

    Layout and utility classes that carry no axis meaning are allowed through
    by name, so the exemption is itself reviewable.
    """
    allowed = _mapped_classes(theme, component) | ALLOWED_UTILITY_CLASSES[component]
    for path in (
        JINJA_DIR / theme / f"{component.title()}.jinja",
        COTTON_THEME_DIR / theme / f"{component}.html",
    ):
        extra = _literal_classes(path.read_text(encoding="utf-8")) - allowed
        assert not extra, (
            f"{path.relative_to(REPO_ROOT)} uses {sorted(extra)}, which primitives.py "
            "does not declare — add it to the map, or to ALLOWED_UTILITY_CLASSES "
            "if it genuinely carries no axis meaning"
        )


#: Classes that appear in a primitive template without belonging to an axis.
#:
#: Keyed **per component** rather than shared. ``label`` needs to wave through
#: tokens as generic as ``ui``, ``text``, ``form`` and ``field`` — Fomantic
#: styles labels by ancestry, so the partial renders the required
#: ``.ui.form > .field`` wrappers. Allowing those package-wide would gut the
#: check for every other primitive, which is the one thing this list must not
#: do. Small and explicit on purpose: an open-ended allowance turns the test
#: above into a no-op.
ALLOWED_UTILITY_CLASSES: dict[str, set[str]] = {
    "button": {
        "is-fullwidth",  # bulma
        "w-100",  # bootstrap
        "expanded",  # foundation
        "fluid",  # fomantic
        "btn-block",  # daisy
        "loading",  # daisy spinner element
        "loading-spinner",
        "spinner-border",  # bootstrap spinner element
        "spinner-border-sm",
    },
    "badge": set(),
    "heading": set(),
    "icon": set(),
    "label": {
        # The required indicator's colour, per theme. Not an axis: `label`
        # takes no variant, and this is the only coloured thing it renders.
        "has-text-danger",  # bulma
        "text-danger",  # bootstrap
        "text-error",  # daisy
        "red",  # fomantic, as span.ui.red.text
        # Structural wrappers Fomantic requires: its only label rule is
        # `.ui.form .field > label`, so the ancestry has to be rendered.
        "ui",
        "text",
        "form",
        "field",
        # daisy puts the size class on this inner span, not the outer label.
        "label-text",
    },
}


def _guard_call(source: str, component: str) -> str:
    """The text of the ``cf_ui_validate`` call for ``component``.

    Both spellings are one call on one line — Jinja's
    ``{{ cf_ui_validate("button", variant=variant, ...) }}`` and Django's
    ``{% cf_ui_validate "button" variant=variant ... %}`` — so the enclosing
    delimiter is enough to bound it. Jinja's whitespace-control dashes are
    optional and some templates carry them.
    """
    match = re.search(r"\{[{%]-?\s*cf_ui_validate\b.*?-?[}%]\}", source, flags=re.S)
    assert match, f"no cf_ui_validate call found for {component}"
    return match.group(0)


def _assert_guard_covers_every_axis(source: str, component: str, where: str) -> None:
    """Calling the guard is not enough — it has to be *passed* every axis.

    A guard invoked as ``cf_ui_validate("heading", level=level, size=size)``
    passes cleanly on ``emphasis="loud"``, which then matches no branch of the
    literal chain and renders unstyled. Presence of the call name is what the
    earlier version of this check tested, and dropping ``emphasis=emphasis``
    survived it.
    """
    call = _guard_call(source, component)
    for axis in PRIMITIVES[component]:
        assert f"{axis}=" in call, f"{where} calls the guard without passing {axis!r}: {call}"


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("component", IMPLEMENTED)
def test_every_jinja_primitive_calls_the_guard(theme: str, component: str):
    """Without the call, an unknown value renders unstyled instead of raising.

    Per theme on the Jinja side, because JinjaX resolves the component
    directly to the theme's file — there is no shared wrapper to hold it.
    """
    jinja = (JINJA_DIR / theme / f"{component.title()}.jinja").read_text(encoding="utf-8")
    assert "cf_ui_validate" in jinja, f"jinja/{theme}/{component} does not call the guard"
    _assert_guard_covers_every_axis(jinja, component, f"jinja/{theme}/{component}")


@pytest.mark.parametrize("component", IMPLEMENTED)
def test_the_cotton_wrapper_calls_the_guard(component: str):
    """Once, on the wrapper — cotton's partials are reached through it.

    ``cotton/cf/<name>.html`` is the only file a consumer's ``<c-cf.button>``
    touches directly, and it is theme-independent, so the check belongs there
    rather than being copied into five partials that could each drop it.
    """
    wrapper = REPO_ROOT / "src" / "cf_ui" / "templates" / "cotton" / "cf" / f"{component}.html"
    source = wrapper.read_text(encoding="utf-8")
    assert "cf_ui_validate" in source
    _assert_guard_covers_every_axis(source, component, f"cotton/cf/{component}")


# ── `for` is not a prop, and saying it is must not fail silently ──────────


def test_a_stray_for_attribute_on_the_cotton_label_raises():
    """``<c-cf.label for="email">`` is the mistake this trip-wire exists for.

    The attribute is ``for_id``, because ``for`` is a Python reserved word and
    JinjaX cannot express it. django-cotton *can*, so the wrong spelling is
    accepted by the compiler and produces a ``<label>`` with no ``for``
    attribute at all — valid HTML, broken label/control association, no error.
    The wrapper routes the value through the guard, which declares no ``for``
    axis, so a non-empty one raises.
    """
    from django.template.loader import render_to_string

    with pytest.raises(PrimitiveConfigError, match="takes no 'for'"):
        render_to_string("cotton/cf/label.html", {"for": "email", "slot": "Email"})


def test_the_correct_spelling_renders_the_for_attribute():
    """The other half of the trip-wire: ``for_id`` must still work.

    Without this, the test above would also pass on a wrapper that rejected
    every label.
    """
    from django.template.loader import render_to_string

    html = render_to_string("cotton/cf/label.html", {"for_id": "email", "slot": "Email"})
    assert 'for="email"' in html


def test_an_absent_for_does_not_trip_the_wire():
    """Django resolves a missing context variable to ``""``, and ``validate``
    skips empty values — which is the only reason the trip-wire can sit in the
    call unconditionally."""
    from django.template.loader import render_to_string

    assert "<label" in render_to_string("cotton/cf/label.html", {"slot": "Email"})


# ── The JSON export the Tailwind plugin reads ─────────────────────────────


def test_the_definition_carries_the_vocabularies_and_classes():
    definition = primitive_definition()
    assert definition["vocabularies"] == {k: list(v) for k, v in VOCABULARIES.items()}
    assert definition["primitives"] == {k: list(v) for k, v in PRIMITIVES.items()}
    assert set(definition["classes"]) == set(THEMES)


def test_the_definition_is_a_copy():
    """Callers mutate freely — ``axis_definition`` makes the same promise."""
    definition = primitive_definition()
    definition["classes"].clear()
    assert set(primitive_definition()["classes"]) == set(THEMES)


def test_the_generated_json_matches_the_module():
    """``just primitives`` output is committed; drift fails here, not in review."""
    import json

    from cf_ui.primitives import PRIMITIVE_DEFINITION_PATH

    on_disk = json.loads(PRIMITIVE_DEFINITION_PATH.read_text(encoding="utf-8"))
    assert on_disk == primitive_definition(), (
        "cf_ui_primitives.json is stale — run `just primitives` and commit the result"
    )


# ── The guard's own behaviour, pinned ─────────────────────────────────────


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ('<a class="button is-primary">', {"button", "is-primary"}),
        ('<a class="btn {{ extra_class }}">', {"btn"}),
        ('<a class="btn {% if x %}btn-sm{% endif %}">', {"btn", "btn-sm"}),
        ('<a class="{{ v }}">', set()),
        ("<a>", set()),
    ],
    ids=lambda v: str(v)[:40],
)
def test_the_literal_class_reader_flags_what_it_claims_to(source: str, expected: set):
    """Pinned because the parity tests are only as good as this parser.

    The third case is the important one: a class inside an ``{% if %}`` *is*
    source text and does survive tree-shaking, so it must be read, while the
    surrounding tag syntax must not.
    """
    assert _literal_classes(source) == expected
