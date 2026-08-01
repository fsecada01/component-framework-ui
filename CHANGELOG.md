# Changelog

## [Unreleased]

## [0.3.0] — 2026-07-31

The primitives layer. 0.2.0 shipped 14 *structural* components — card, modal,
navbar, table — and nothing underneath them, which is the layer an app
actually uses hundreds of times. This release adds it: seven primitives across
five themes in both template sets, on one shared vocabulary.

**Upgrading from 0.2.0 on the daisy theme:** `cf_ui_head` now emits Tailwind's
Play CDN script alongside the daisyUI stylesheet (#56). If you already have a
real Tailwind build supplying both layers, set `CF_UI_DAISY_CDN = "off"` to
keep the previous single-tag output. Every other theme is unchanged.

### Changed — the release wheel guard is derived, not counted (#63)

- **`release.yml` checked the wheel against hardcoded floors and they had gone
  stale.** It asserted `>= 14` JinjaX templates, cotton wrappers and cotton
  partials — figures from 0.1.0, when 14 components in one set was the whole
  package. By 0.3.0 the real counts are 21 wrappers and 105 partials, so a
  packaging regression dropping all seven primitives from all five themes
  would have left exactly 14 and **passed**. The list of required static
  assets had also never picked up `cf_ui_primitives.json` from #52. The guard
  now derives its expectation from the source tree and asserts the wheel
  contains every shipped template and asset — it cannot go stale, and it fails
  on one missing file rather than only on a missing fourteen. It also checks
  that its own scan found something first, because a guard whose input
  silently becomes empty passes vacuously, which is the failure being replaced.

- **The version was declared twice with nothing comparing them.**
  `pyproject.toml` and `src/cf_ui/_version.py` both carry it, and the tag-match
  step reads only the former — so a bump that missed `_version.py` would
  publish a correctly-named wheel whose `cf_ui.__version__` reported the
  previous version, permanently, with every gate green. `tests/unit/test_version.py`
  now asserts they agree, in the unit suite rather than at release time,
  because the drift is introduced when the bump is written.

### Decided — layout is out of scope; cf-ui ships no grid (#55)

- **Tier 3 (`grid`) is closed as won't-do, and `docs/primitives.md` now says
  so with the reasoning** so the question does not come back as a bug report.

- **The premise it was raised on was false.** #55 assumed four of five themes
  ship a 12-column grid and only daisyUI was the odd one out. Checked against
  upstream: **Fomantic's grid is 16 columns**, so `span="6"` would mean half
  the row on four themes and three-eighths of it on Fomantic — a different
  idea, not a different spelling, and the failure would be silent. And
  **Bulma's `mobile` tier is a max-width cap** while every other framework's
  ladder is min-width, so `at="mobile"` would have to mean "from here up" on
  four themes and "below here" on the fifth. Every other axis cf-ui absorbs
  maps *n* names onto one concept; this one has no single concept underneath.

- **The reduced (non-responsive) version is not a fallback.** A three-column
  layout that stays three columns on a phone is broken rather than simpler, so
  consumers would immediately reach for the responsive axis — the part that
  does not work. And Fomantic's column count breaks the reduced version just
  as thoroughly, because it is not the responsive axis. The Tailwind
  literal-class cost (60 spelled-out branches per template, duplicated in
  `primitives.py`) is the third strike, not the first.

- **The cost is stated rather than hidden.** "Switching frameworks means
  changing `CF_UI_THEME` in one place" now carries a named exception: layout
  does not switch. The docs say what to do instead — the framework's own
  vocabulary, or plain CSS Grid / flexbox for theme-independent layout.

### Added — primitives Tier 2: `box` and `prose` (#54)

- **Two container primitives, on all five themes, in both template sets.**
  `<Cf:Box>` / `<c-cf.box>` is a plain bordered container — one element, no
  imposed header/body/footer, which is what separates it from `card`.
  `<Cf:Prose>` / `<c-cf.prose>` is a typographic reset for a block of
  server-rendered or user-supplied markup. `box` takes `variant`; `prose`
  takes `size`. A container's size is its content's business, and a
  typographic reset has no colour, so neither takes more.

- **Named `box` and `prose`, not `surface` and `content`.** `box` is Bulma's
  own class name; `surface` is Material vocabulary no shipped framework uses.
  `content` was rejected twice over: it collides with Bulma's own `.content`
  class, and `content` is already the prop every Jinja primitive uses for slot
  text, so `<Cf:Content content="…">` would have been the spelling.

- **Fomantic's `primary` and `secondary` are not colours on a segment.** They
  are its *emphasis* variation — `.ui.primary.segment` renders a subdued
  treatment, not a brand fill. The variant maps to real hues (`blue`, `grey`,
  `green`, `yellow`, `red`, `teal`) instead, because the one theme where the
  vocabulary appears to match by name is the one theme where matching it would
  be wrong. Verified against Fomantic's own SCSS rather than assumed.

- **`prose` is honest about where it does nothing.** On Bootstrap and
  Foundation it emits no class at all, and that is correct rather than
  missing: both style bare `h1`-`h6`, `p` and `ul` globally, so the reset this
  component exists to scope is already in effect. Fomantic is different and
  worse — it styles headings and paragraphs globally but ships **no** bare
  `ul`, `ol` or `table` rule, so lists and tables inside a prose block fall
  back to browser defaults and no scoping class fixes it. Documented in
  `docs/primitives.md` with the workaround that does work, rather than papered
  over with a cf-ui-authored type scale.

- **On daisy, `prose` requires `@tailwindcss/typography`** — the class is from
  that plugin, not from daisyUI and not from Tailwind core. Declared as a
  requirement in `docs/daisyui.md`. Without it the block renders unstyled,
  which is the benign class-valued failure mode rather than broken markup.

- **`docs/escaping.md` now states the sanitization contract outright.**
  `prose` is the first primitive whose purpose is wrapping caller-supplied
  markup. Mechanically nothing changed — it is still slot-based and cf-ui's
  own output is still escaped — but the thing that had never been written down
  is that **cf-ui does not sanitize**. A caller reaching for `Markup` /
  `mark_safe` has taken that on, and `nh3` or `bleach` is what does the job.

### Fixed — two test guards that could not fail

- **The theme-dispatch test was passing on whitespace.** It compared raw
  rendered strings across the five themes and required all five to differ. A
  `{% comment %}` block leaves its own blank lines behind, so two partials
  emitting byte-identical markup still landed in different buckets on newline
  count alone. Proven by mutation: gutting a partial's entire class chain left
  the test green. It now compares collapsed markup, and allows two themes to
  coincide only when their entry in `CLASSES` proves they agree — so `prose`
  rendering alike on three themes passes for a stated reason, while a partial
  that silently drops an axis still fails.

- **`IMPLEMENTED` was a hand-written tuple**, which made adding a primitive a
  silent-coverage trap: register it in `PRIMITIVES` and `themes.COMPONENTS`,
  forget this one line, and its templates shipped with zero parity and guard
  coverage without anything failing. It is now derived from the intersection
  of the two, so the failure mode inverts — a primitive registered without
  templates fails loudly instead of quietly not being checked.

### Fixed — daisyUI's CDN recipe was missing its utility layer (#56)

- **`cf_ui_head(theme="daisy")` shipped half of daisyUI's own documented CDN
  recipe, and that half silently drops every layout utility (#56).** DaisyUI
  is a Tailwind *plugin* — its CDN stylesheet is the component layer only
  (`.btn{`, `.card{`), never the utility layer (`.flex{`, `.w-full{`,
  `.gap-4{`) that the shipped daisy templates depend on for layout. A
  consumer following the quickstart with `CF_UI_THEME = "daisy"` got buttons
  and cards that looked right sitting in a layout that did not work, with no
  error to point at the cause. daisyUI's own CDN docs
  (<https://v4.daisyui.com/docs/cdn/>) pair the stylesheet with Tailwind's
  Play CDN script for exactly this reason; cf-ui was shipping only the first
  tag. `cf_ui_head` / the `cf_ui_head` Jinja macro now emit both, in the
  vendor's order, gated by a new `CF_UI_DAISY_CDN` setting (`"play"` default,
  `"off"` for a consumer with a real Tailwind build supplying both layers
  itself). An invalid value now fails at Django startup, matching
  `CF_UI_THEME` and `CF_UI_COMPOSITION`. The other four themes are
  unaffected — this only ever touched the daisy branch of `cf_ui_head`. See
  [DaisyUI](docs/daisyui.md) for the full recipe and why `"play"` is the
  default rather than `"off"`.

### Added — a primitives layer: button, badge, heading, label, icon (#52)

- **Five new components, on all five themes, in both template sets.**
  `<Cf:Button>` / `<c-cf.button>`, and the same for `Badge`, `Heading`,
  `Label`, `Icon`. cf-ui shipped 14 *structural* components and no primitives,
  which is why adoption stalled: measured against a real consumer, `button`
  was the single most-used CSS-framework class in the codebase (204 uses) and
  cf-ui had nothing for it, while `modal`, `tabs`, `panel` and `breadcrumb`
  had zero uses between them.

- **`src/cf_ui/primitives.py` is the closed vocabulary and the class map.**
  `variant`, `size`, `state`, `level`, `emphasis` and `type` are fixed sets; a
  value outside one raises `PrimitiveConfigError` naming the values that would
  have worked. Which primitive accepts which axis is declared, so
  `<Cf:Badge state="loading">` raises rather than rendering a badge with no
  loading state.

- **Every axis declares what its value *becomes*: a class, a tag, or an
  attribute.** `AXIS_KINDS` is that declaration, and it is what makes the
  empty-value rule derivable rather than case-by-case. Django resolves a
  missing context variable to `""` and the cotton wrappers forward props
  unconditionally, so an absent class-valued axis has to be benign — it yields
  an unstyled element, which is exactly what a missing `variant` should do. An
  absent *tag*- or *attribute*-valued one does not: an empty `level` has no
  `<h?>` to render, so it raises and the message says which kind of thing was
  missing and what to pass. `CLASS_VALUED` is derived from `AXIS_KINDS`, no
  theme may map a non-class axis, and both are enforced by tests — which is
  also how `type` (`button` / `submit` / `reset`, the HTML default being
  `submit` inside a form) got a vocabulary and a guard instead of passing
  through unchecked.

- **`ALIASES` names the props whose HTML spelling cf-ui cannot use.**
  `<c-cf.label for="email">` used to render valid HTML with no `for` attribute
  at all: `for` is a Python reserved word so the prop is `for_id`, and
  django-cotton silently discards attributes a component does not declare. The
  wrapper now forwards the HTML spelling into the guard purely so it can be
  rejected, and the error names `for_id`. This catches the *declared*
  confusions, not arbitrary typos — `docs/primitives.md` says so plainly.

- **The classes are spelled out longhand in the templates, on purpose.**
  daisyUI compiles through Tailwind, whose scanner reads source *text* — a
  class assembled at render time (`btn-{{ variant }}`, or one returned from
  Python) is tree-shaken out of the build with no error and an unstyled
  element as the only symptom. So `primitives.py` and the templates hold the
  same knowledge twice, and a bidirectional parity test in
  `tests/unit/test_primitives.py` fails the build the moment they disagree —
  in either direction. `classes_for()` exists for tests, docs and
  outside-the-templates consumers; nothing in the shipped templates calls it.

- **`static/cf_ui/cf_ui_primitives.json`** is generated from the module by
  `just primitives`, the way `cf_ui_axes.json` is generated from `axes.py`,
  and a drift test fails if the committed copy is stale.

- **Escaping and accessibility are decided once, in the component.** A
  disabled `<a>` renders `aria-disabled="true"` and *no* `href` — an anchor
  without one is not focusable or activatable, so this is the only spelling
  where "disabled" is more than cosmetic. An icon is either decorative
  (`aria-hidden="true"`) or named (`role="img"` plus `aria-label`), never
  both, and `role="img"` makes it a leaf so the caller's glyph markup is not
  descended into. Primitives take slot content rather than markup props, so
  `docs/escaping.md` needs no new rule.

- **`docs/primitives.md`** documents the shared contract, composition, the
  per-theme places an axis is legitimately inert, and why the classes are
  longhand. Tier 2 (`box`/`surface`, `prose`) and Tier 3 (`grid`) are tracked
  separately so this could ship on its own.

### Added — djLint formats both template trees, one attribute per line

- **`prek` now reformats and lints `templates/cotton/**.html` and
  `templates/jinja/**.jinja`.** Four hooks pinned at djLint v1.43.1, two per
  tree, because `profile` is one global setting and the two trees are
  different languages. Settings live in `[tool.djlint]`; `just
  format-templates` and `just lint-templates` run the same thing by hand, and
  `just check` now includes the lint pass.

- **`single_attribute_per_line = true` is the point of the exercise.** A
  cf-ui template's entire contract lives in its opening tag — `<c-vars>`
  declares every prop, and a theme partial's element carries a literal
  `{% if %}` chain per axis. Authored on one line, because Django has no
  whitespace-control syntax and the safe default was "emit no whitespace", a
  wrapper's prop list was a 100-character run read character by character.
  107 cotton and 95 jinja templates were reformatted.

- **Checked rather than assumed.** Whitespace *between* attributes is
  insignificant in HTML; whitespace *inside* a `class` value is not — it
  changes the rendered bytes and defeats every substring assertion in the
  suite — so djLint is not allowed near the class chains. All 190 primitive
  renders (5 themes × 19 components × 2 engines) came out byte-identical with
  whitespace stripped, and the parsed DOM matched except for djLint adding a
  space after `;` in inline `style` attributes. One assertion did depend on
  layout — `"required>" in html`, which relied on the attribute being last
  before the bracket — and is now anchored to the `<input>` tag itself, which
  is what it always meant.

### Fixed — multi-line `{# #}` comments rendered into the page

- **Six shipped cotton partials leaked their own source comments as page
  text.** Django's comment regex is `\{#.*?#\}` without `DOTALL`: `{# #}` is
  single-line only, so a comment opened on one line and closed on another
  never forms a comment token and every line in between is emitted verbatim.
  Five bootstrap partials and one daisy partial were affected —
  `checkbox-group`, `modal`, `navbar`, `panel`, `progress` and
  `daisy/navbar` — each shipping a paragraph of rationale prose about z-index
  stacking or Tailwind layer ordering straight into the consumer's HTML. All
  six now use `{% comment %}`, and
  `tests/unit/cotton/test_comment_syntax.py` fails the build on a recurrence.
  Found while writing a primitives wrapper that made the same mistake.

### Changed — dependencies resolve from PyPI, not from git (#50)

- **Dropped the `[tool.uv.sources]` git pin for `component-framework`.** It
  never travelled into wheel metadata, so no consumer was affected — but CI
  runs `uv pip install -e ".[dev]"`, which *does* honour the sources table, so
  every test run resolved the dependency from git master rather than from a
  release. Concretely: the dev environment was serving **0.6.0b0 from commit
  2833311** while 0.6.0 was live on PyPI. The suite was not exercising what
  users install. The pin was correct while nothing was published; the failure
  mode was forgetting to remove it afterwards.

- **Raised the floor to `component-framework>=0.6`.** 0.6.0 is the only final
  release; 0.4.x and 0.5.x exist only as `b0` tags, so `>=0.4` named a
  compatibility range that was never published and never tested. It also
  invited exactly the pre-release fallback that produced the `0.6.0b0` above —
  a specifier without a pre-release marker resolves to one only when no final
  exists.

- **`tests/unit/test_dependency_sources.py` is the guard**, on both halves.
  It fails if any dependency is resolved from a git, URL, or path source
  (`workspace` and `index` entries are allowed — those are layout, not a
  substitute for a release), if the floor slips below the first published
  final, and — reading `direct_url.json` per PEP 610 — if the *installed*
  distribution came from a VCS. That last one matters because a clean
  `pyproject.toml` says nothing about a stale venv still serving whatever the
  pin last resolved; it was red against this repo's own environment until the
  reinstall.

## [0.2.0] — 2026-07-31

First release published to PyPI. Five themes instead of two, an axis layer
that enforces what it claimed, components that render on Litestar at all, and
two security fixes on the Jinja path. **Three breaking changes** — listed
first, because a 0.x version number carries no semver promise to read them
off:

- Components render on the Litestar path (#42). `<Cf:Card>` previously reached
  the browser as literal text — no exception, no output, a 200 response. An
  app that worked around this by hand-writing the markup should drop the
  workaround.
- Cf-ui's Jinja templates escape their own output (#36). Anything previously
  interpolated raw through a component now renders as entities; a prop
  deliberately carrying markup must be `markupsafe.Markup`.
- The axis layer validates token *values*, drops the `--spacing` alias, and
  validates by default in every exported generator (#20).

### Fixed — BREAKING for Litestar: components actually render there now (#42)

- **`<Cf:Card>` reached the browser as literal text on the Litestar path.** No
  exception, no output, a 200 response — the worst possible failure shape. The
  installer appended a template directory and registered axis globals but
  never built a JinjaX catalog, so Litestar's Jinja2 environment had never
  heard of the component tag.

  `Catalog(jinja_env=env)` does not convert the environment it is given: it
  builds its own, copies extensions/globals/filters across, and writes
  `catalog` back into the original. Three things have to land on Litestar's
  environment directly — the `JinjaX` extension, a catalog built over that
  environment, and a `__prefix` binding. JinjaX rewrites `<Cf:Card>` into
  `catalog.irender("Cf:Card", __prefix=__prefix, …)` and binds `__prefix`
  per-component while rendering *inside* a component, so a page template
  rendered by Litestar has no binding and raises `'__prefix' is undefined`.

- **`{% from "cf_ui/assets.jinja" import … %}` raised `TemplateNotFound` on
  Litestar** — the macros are a sibling of `templates/jinja/`, and only
  `templates/jinja/<theme>` was on the search path. Both that directory and
  the package template root are now registered.

- **`jinjax>=0.41` added to the `[litestar]` extra**, matching
  `component-framework`, whose litestar extra has always listed it.

- **Litestar had no integration or E2E coverage at all** — only `MagicMock`
  unit tests, which cannot observe a render, which is why both defects
  shipped. `tests/integration/test_litestar_components.py` runs a live
  Litestar app through its real template engine: component tags, self-closing
  tags, the assets macros, the axis globals, a non-default theme, and #36
  escaping on a path where Litestar does not enable autoescaping. Four of the
  six fail with the catalog install removed.

### Fixed — documented JinjaX attributes that never interpolated (#42)

- `header="{{ title }}"` does **not** interpolate in JinjaX; the braces arrive
  at the component as literal text with no error. Computed values need the
  colon binding, `:header="title"`. Four published samples in the quickstart
  and use-cases pages had the brace form. `tests/unit/test_docs_samples.py`
  now fails the build on a braced attribute in any `Cf:` tag, while leaving
  django-cotton's `{{ }}` alone — there it is ordinary Django syntax and
  correct.

### Packaging (#43)

- **Added a `LICENSE` file.** `pyproject.toml` declared `license = {text =
  "MIT"}` while the repository carried no license text, so the wheel shipped
  none. The built wheel now carries `License-File: LICENSE`.
- **Added the classifier set** — Development Status, Intended Audience,
  License, Python 3.11–3.14, Framework and Topic entries. There were none at
  all, which is what the PyPI page is built from.

### Release automation (#45)

- **Added `.github/workflows/release.yml`.** A `v*` tag builds, validates, and
  publishes to PyPI via **trusted publishing** — the job mints a short-lived
  OIDC token that PyPI exchanges for an upload token scoped to this project.
  No API token is created, stored, or rotated, so there is no repo secret to
  leak. The upload is a separate job behind a `pypi` environment, so
  protection rules can require a review before anything reaches PyPI.
- **The build job refuses to hand off a wheel that is missing its templates.**
  cf-ui is templates; they live inside the package so hatchling picks them up
  with no explicit include, which is exactly what would make a regression here
  quiet — a packaging change that dropped them would produce a wheel that
  installs cleanly, imports cleanly, and renders nothing. The job counts the
  JinjaX templates, the cotton wrappers and theme partials, and asserts
  `assets.jinja` and the generated axis assets are present. It also checks the
  tag against `pyproject.toml`'s version and runs `twine check`, because a bad
  upload can only be yanked, never replaced.

### Documentation — a published site, and three broken README samples fixed (#39)

- **A MkDocs + Material site now builds from `docs/` and deploys to GitHub
  Pages** on every push to `master`; pull requests build without deploying, so
  a fork PR can never publish. The build runs with `--strict` plus
  `validation.anchors: warn`, which makes a dead internal link *or* a dead
  anchor fail CI — MkDocs reports missing anchors at INFO by default, which
  would have let them through. New pages: Installation, Quickstart, Getting
  started, Use cases, Components, Escaping. The five pre-existing guides
  (theming, tailwind-plugin, accessibility, bootstrap, daisyui) are now nav
  entries and needed no rewriting, because MkDocs' default `docs_dir` is
  already where they live — README's `docs/<page>.md` links keep resolving on
  GitHub.

- **`from jinjax import ComponentCatalog` never worked.** jinjax exports
  `Catalog`; that import raised `ImportError` on the first line of the
  README's FastAPI quickstart. Fixed.

- **`<CfCard>` never worked either.** `Cf` is a JinjaX *prefix* and the prefix
  separator is `:`, so the tag is `<Cf:Card>` and the render name is
  `"Cf:Card"`. Both `<CfCard>` and `<Cf.Card>` raise `ComponentNotFound`. The
  wrong form was in README and in the CLAUDE.md naming table; both are fixed,
  and `tests/unit/test_docs_samples.py` now renders all three forms so the
  claim is executable rather than asserted.

- **The README's Django settings sample did not parse** — an elided
  `INSTALLED_APPS = [ ... "cf_ui.django.CfUiConfig" ]` is `Ellipsis` followed
  by a string with no comma. Rewritten.

- **`tests/unit/test_docs_samples.py` is the guard against all of the above
  recurring.** It extracts every fenced block from `README.md` and `docs/*.md`
  (including the indented ones inside `=== "Tab"` containers), requires each
  `python` block to parse, resolves every `from … import …` against the real
  installed module, and checks every `Cf:Name` / `<c-cf.name>` reference
  against the shipped component set. Two non-vacuity pins keep it honest: one
  asserts the import check did not degenerate into all-skips, another that
  both component regexes still match something.

- The Litestar quickstart imports `JinjaTemplateEngine` from
  `litestar.plugins.jinja`; the `litestar.contrib.jinja` path has warned since
  Litestar 2.22 and goes away in 3.0.

- `just docs` serves the site locally, `just docs-build` runs the exact
  `--strict` build CI does. New `[docs]` extra; `[dev]` includes it.

### Fixed — extras that did not match their own documentation (#47)

- **`django-cotton>=0.9` admitted versions that cannot work.** All 14 cotton
  wrappers use `<c-vars>`, and `<c-props>` was renamed to `<c-vars>` in
  django-cotton **0.9.6** — so the floor resolved 0.9.0 through 0.9.5, on
  which every wrapper installs cleanly and then silently drops every prop.
  Nothing surfaced it because the dev environment resolves 2.7.2. The floor
  is now `>=2.0`, the major series actually tested, rather than the bare
  0.9.6 syntax minimum that would claim two years of untested range.
  `CLAUDE.md` said the rename landed "in 2.x"; that was wrong, and is the
  reason the floor looked defensible.

- **The `[litestar]` extra was documented without JinjaX** in both `README.md`
  and `docs/installation.md`, long after it was added to `pyproject.toml`.
  Harmless to installs, but actively misleading: the `[fastapi]` line above it
  *does* name JinjaX, so the pair read as "Litestar is the non-JinjaX path" —
  the exact misconception #42 was about. Both files now name it, and say why
  Litestar needs both: they are layers, not alternatives. Litestar's
  `JinjaTemplateEngine` owns the Jinja2 environment and cf-ui installs a
  JinjaX catalog onto it, while on the FastAPI path the catalog owns the
  environment outright and pulls Jinja2 in transitively.

- The README also described `[fastapi]` without `uvicorn` or
  `python-multipart`, which `docs/installation.md` had listed all along.

- **`tests/unit/test_extras_docs.py` is the guard.** It reads
  `optional-dependencies` out of `pyproject.toml` and diffs it against the
  extras described in `README.md` and `docs/installation.md` — the reference
  table must carry every public extra, and either file must describe
  completely whatever it describes at all. `test_docs_samples.py` could not
  see any of this: it validates Python samples and link targets, and these
  are prose claims about packaging metadata. Two traps are pinned as
  behaviour: the extra's own `` `[django]` `` marker must not stand in for the
  Django distribution, and `django` must not be found inside `django-cotton`.
  Both passed a earlier cut of the guard, and both are now regression cases.

### Security — BREAKING: cf-ui's Jinja templates now escape their own output (#36)

- **Every `{{ … }}` in a cf-ui template emitted raw output on the FastAPI and
  Litestar paths.** A request-controlled value carrying a double quote closed
  the attribute it was rendered into and could open one of its own, event
  handlers included. `jinjax.Catalog` builds
  `Environment(undefined=StrictUndefined)` — autoescape defaults to `False` —
  and adopts the setting only from a caller-supplied `jinja_env`; Litestar's
  `JinjaTemplateEngine` does not enable it either. Django/cotton consumers
  were never affected; Django autoescapes by default.

  This is the other half of #32. That ticket stopped `tab.id` being *evaluated*
  as JavaScript by routing it through `data-cf-tab`, which was the right fix and
  stands — but it moved the value from an expression into an attribute value,
  and attribute-value safety is this one. It was never specific to tabs:
  `hx-get="{{ tab.url }}"`, `id="{{ id }}"` and the text nodes were all exposed
  the same way.

  **The mechanism is in-template, on purpose.** Every component template wraps
  its body in `{% autoescape true %}`, so the guarantee is a property of the
  files cf-ui ships rather than of any environment: it holds on a bare
  `Catalog()`, on Litestar's plain-Jinja path, and for a consumer who registers
  the templates with `add_folder` and never calls `install_cf_ui`. The
  installers do not touch the environment's `autoescape` at all — the app's
  policy, `select_autoescape` callables included, stays the app's. An
  environment-level fix was tried first and rejected on evidence: setting the
  flag unconditionally destroyed caller policies; setting it only-when-off
  reopened the hole for `select_autoescape(["html"])`, which answers `False`
  for `.jinja` files; and either way it was order-dependent, because
  `autoescape` is read at compile time and JinjaX caches compiled components —
  a component rendered before install stayed unescaped for the process
  lifetime while the flag read `True`. In-template blocks have none of those
  failure modes. The `assets.jinja` macros carry the same blocks inside each
  macro body (a file-scope block would stop the macros exporting).
  `tests/unit/test_autoescape.py` guards presence and placement in all 70
  templates so a new theme cannot ship without them.

  **Migration.** Output that was previously interpolated raw through a cf-ui
  component now renders as entities. The realistic surface is small —
  components take structured props, and JinjaX hands slot content over as
  `Markup` — but it is a behaviour change, not a patch. A prop that
  deliberately carries real markup must be wrapped in `markupsafe.Markup`;
  cf-ui's own E2E gallery needed exactly one such change (a `footer=` prop
  carrying a button). There is no opt-out flag: escaping travels with the
  templates.

- **The axis globals are marked safe at the Jinja boundary.**
  `cf_ui_axis_attrs()` and `cf_ui_axis_style()` render markup — five attributes
  and a `<style>` element — so `build_axis_globals` now wraps them in `Markup`.
  `assets.jinja` did pipe both through `|safe`, but a value that is only safe
  when every caller remembers a filter is not a guarantee, and the Django side
  has always marked safe at the templatetag for the same reason. `markupsafe` is
  imported inside the function rather than at module scope: it arrives with
  `jinja2`, which is a `fastapi`/`litestar` extra, while `cf_ui.templatetags`
  imports `cf_ui.axes` on the Django-only path where neither is installed.

- **Two test fixtures were asserting escaping they never enabled.**
  `select_autoescape(["html"])` keys off the file *extension*, and cf-ui's Jinja
  templates are `.jinja`, so it resolved to `False` in
  `tests/unit/jinja/conftest.py` and `tests/unit/test_axis_jinja.py` — a fixture
  that reads as though it escapes and does not, which is worse than one that
  plainly does not. The three fixtures added by #32 listed
  `["html", "jinja"]` and did escape, so the suite disagreed with itself about
  what shipped.

  All five now build their environment through `tests/jinja_env.py`, which
  sets `autoescape=False` deliberately: cf-ui's templates escape their own
  output, so any escaping a test observes can only have come from the template
  under test — a harness that autoescaped would mask a template that lost its
  block. `tests/integration/test_jinja_autoescape.py` is the tier that was
  missing entirely, and asserts the injection cases against a bare `Catalog`
  for the same reason.

### Added — Fomantic UI theme (#24)

All 14 components in both template sets, replacing the `PLANNED.md` stub.
`CF_UI_THEME = "fomantic"` (Django) or `theme="fomantic"` (FastAPI/Litestar)
now resolves; it was rejected at startup before. The CDN entry and pinned
version (`fomantic-ui@2.9.3`, `dist/semantic.min.css`) already existed and were
verified to still resolve.

- **CSS only — no jQuery, and no Fomantic JS.** Fomantic's Modal, Tab,
  Accordion and Dropdown are jQuery plugins, which makes this the most
  JS-dependent of the five themes. Loading them would mean a *styling* choice
  silently changed a consuming app's dependency graph, so the theme uses
  Fomantic's classes and markup structure only and Alpine drives every
  behaviour, exactly as it does for Bulma and DaisyUI. A unit test scans all 28
  templates and an E2E test checks the delivered page and the live `window`.

- Consequences of that, where they are not obvious from the markup:
  - **Modal** renders its own `.ui.dimmer`. Fomantic normally injects it from
    `$('.ui.modal').modal('show')`; here the dimmer and the modal each take
    `active` from the same Alpine `open`, since both are `display:none` without
    it.
  - **Panel** binds `active` as a class rather than relying on `x-show` alone.
    `.ui.accordion .title ~ .content:not(.active)` is `display:none`, so Alpine
    merely dropping its inline style would leave the panel hidden.
  - **Select** is a plain `<select class="ui fluid selection dropdown">`.
    Fomantic's `ui dropdown` is a JS-built widget over a hidden select;
    reproducing its DOM by hand would be a combobox nobody could drive.
  - **Tabs** puts its panel in a `ui bottom attached segment`, not `.ui.tab` —
    `.ui.tab` is `display:none` until Fomantic's Tab module adds `active`.
  - **Navbar** uses `ui stackable menu`, Fomantic's CSS-only responsive
    collapse. Its burger reports state through `aria-expanded` and the `active`
    class but hides nothing, because Fomantic's collapse is a Sidebar/Dropdown
    JS module that cf-ui does not load.
  - **Field errors** use `ui basic red pointing prompt label`, not
    `ui error message` — the latter is `display:none` until the *form* itself
    carries `.error`.
  - **Progress** is a div, so `role="progressbar"` and `aria-valuenow` /
    `aria-valuemin` / `aria-valuemax` are written out, and the bar width and
    `data-percent` are rendered server-side. The percentage is also clamped to
    `0..100`: Bulma and DaisyUI render a real `<progress>`, which the browser
    clamps for both painting and the accessibility tree, whereas a div would
    take `width: 150%` and report `aria-valuenow="150"` against a max of 100.
    The ARIA is stated in percent so it agrees with the visible label.

- Accessibility is at parity with every other theme, not a reduced subset: the
  parametrized cases in `tests/unit/test_accessibility.py` now run against five
  themes rather than four, with no assertion weakened.

- Tab ids reach Alpine through `$el.dataset.cfTab`, never as interpolated
  expression source (#32). The tree-wide guard that shipped with that fix reads
  its theme list from `THEMES`, so it covered this theme the moment the registry
  entry landed — and did not pass until the templates were corrected.

- **The last `PLANNED.md` stub is gone.** Every directory under `templates/` is
  now a real theme, which retires the "a directory exists but is not selectable"
  test that has existed in some form since #6. What it protected is stated
  directly instead: `resolve_theme` and `CfUiConfig.ready()` answer from
  `THEMES`, not from the filesystem.

### Security — tab ids no longer reach Alpine as expression source (#32)

- **A request-controlled `tab.id` executed as JavaScript on page load.** Each
  tabs template spliced it into four attributes Alpine evaluates as source
  (`:class`, `:aria-selected`, `:tabindex`, `@click.prevent`), so an id
  containing an apostrophe closed its string literal, ran, and reopened it —
  no user interaction, and the surrounding expression still parsed, so Alpine
  logged nothing. Sixteen sites across bulma and daisy, plus eight more each in
  bootstrap and foundation, which carried the same fix in on their own branches
  (#29, #30) rather than merging with a known injection. Fomantic follows the
  same way. Fixing it in two themes now instead of five later is the whole
  reason this went ahead of the expansion epic.

  HTML escaping does not mitigate it and could not: the parser decodes `&#x27;`
  back to `'` while building the DOM, and Alpine reads the decoded attribute.
  The value has to stop being source. Every binding now reads
  `$el.dataset.cfTab` — `data-cf-tab` was already on each tab for the roving
  tabindex, so the fix adds plumbing only for the wrapper element some themes
  put the active class on.

  This closes the *execution* path, not every use of a hostile id. Attribute
  escaping is a separate guarantee, which `install_cf_ui` did not make when
  this landed — a double quote in `tab.id` could still break out of
  `data-cf-tab` itself under FastAPI/Litestar. Closed by #36, below, in the
  same release; Django/cotton was never affected.

  `cf_ui_alpine.js` already stated this rule in `initTabs()` and already
  followed it for `data-cf-active`; it simply was not carried one level down.
  `tests/unit/test_alpine_expression_safety.py` now enforces it over every
  template in the package, so a sixth theme cannot reintroduce it by copying a
  fifth, and `tests/e2e/test_alpine_injection.py` proves the payload is inert in
  a real browser — asserting both that it did not run and that the bindings did
  evaluate, since a fix that made Alpine throw would satisfy the first alone.

### Added — Foundation 6 theme (#23)

All 14 components in both template sets, replacing the `PLANNED.md` stub at
`templates/jinja/foundation/` and creating `templates/cotton/_themes/foundation/`.
`foundation` is now accepted by `CF_UI_THEME` and by `install_cf_ui(theme=…)`;
`_CDN_CSS` and `_DEFAULTS` already carried it at `6.7.5`.

- **CSS only, and no jQuery.** Foundation's interactive components — Reveal,
  Tabs, Accordion, Dropdown Menu — are jQuery plugins. Loading them would make a
  theme choice change a consuming app's dependency graph, and would put a second
  owner on state `cf_ui_alpine.js` already holds. The templates use Foundation's
  classes and markup structure; every piece of state is wired through the
  existing Alpine components. Asserted per component rather than left to prose.

- **Three places where Foundation's CSS assumes its JS is present**, and what
  each does instead:
  - `.reveal` has no open-state class — Foundation's Reveal writes
    `style.display` directly — so the modal toggles inline display rather than a
    class, and the E2E tier asserts visibility instead of a class list.
  - `.accordion-content` is `display: none` with no un-hiding rule in the
    stylesheet, so the panel stays off the accordion entirely and `x-show` owns
    display, seeded from `data-cf-open`. Same shape as the bug #21 fixed.
  - The navbar collapse uses `hide-for-small-only`, not `hide`: `hide` would
    collapse the desktop menu too, and with Alpine off no class is emitted at
    all, so the menu is simply visible.

- **`aria-selected` on a tab is load-bearing for appearance here.**
  `.tabs-title > a[aria-selected=true]` is the rule that restyles the selected
  tab; `.is-active` on the `<li>` alone changes nothing visually. Both are
  rendered server-side and both keep their Alpine binding. The tab panel is
  `.tabs-content` rather than `.tabs-panel`, because this widget has one
  always-shown HTMX-swapped panel, and `.tabs-panel` is hidden until
  `.is-active` picks one of several siblings.

- **Variant vocabulary maps inside the partial**, as designed: Foundation's
  callout uses bare `alert` / `success` / `warning` with no `is-` prefix, and has
  no `info` variant — `type="info"` maps to `primary`. Public prop values are
  unchanged. `progress` needs a `.progress-meter` child because 6.7.5 does not
  style a native `<progress>`; a zero `max` yields 0% rather than a
  `ZeroDivisionError` on an empty result set.

- Tab ids reach Alpine through `$el.dataset.cfTab`, never as interpolated
  expression source (#32) — applied here so the theme does not land with the bug
  and need patching twice.

### Added — Bootstrap JS decision record and a version tripwire (#33)

- **`docs/bootstrap.md`.** The CSS-only, Alpine-driven stance was a decision
  taken during #22 and recorded nowhere a consumer or maintainer would look.
  This states it, gives the three reasons in the order they mattered, and — the
  part that was actually missing — answers "may I use a Bootstrap component
  cf-ui does not ship?". Bootstrap 5.3.3 ships 12 JS-driven components; cf-ui
  replaces four of those plugins across five of its own components, so eight are
  uncovered. The page names them and gives three ways forward, with the one hard
  rule: never put a `data-bs-*` attribute on a cf-ui component, because
  Bootstrap's JS and `cf_ui_alpine.js` would then own the same state and the
  failure is load-order dependent and intermittent.

  It also records the per-theme behaviour driver as considered-and-deferred, so
  the option is not relitigated from scratch, and states why: an abstraction for
  a problem no consumer has reported, whose strongest motivation has an API that
  does not exist yet.

- **`tests/unit/test_bootstrap_version_pin.py`.** "Monitor for Bootstrap 6" is
  not a commitment that survives; a red test is. `_DEFAULTS["bootstrap"]` is the
  single place the major version is stated, and this fails the moment it leaves
  the `5.x` line, with a failure message that *is* the checklist of what to
  re-evaluate. Same pattern #17 established for Tailwind.

  What it points at, verified against `v6-dev` rather than release notes:
  `_modal.scss` is replaced by `_dialog.scss` with no `.modal*` selector left,
  `modal.js` by `dialog.ts` on `HTMLDialogElement.showModal()`, and the JS
  surface is growing rather than shrinking. cf-ui's bootstrap modal templates
  carry eight `modal-*` references each, so the markup breaks at v6 on the CSS
  alone — which is the useful part, because it means the JS question gets
  re-asked for free at the moment it is cheapest to answer.

### Added — Bootstrap 5 theme (#22)

All 14 components in both template sets, replacing the `PLANNED.md` stubs at
`templates/jinja/bootstrap/` and `templates/cotton/bootstrap/`. `bootstrap` is
now accepted by `CF_UI_THEME` and by `install_cf_ui(theme=…)`; `_CDN_CSS`,
`_DEFAULTS` and `assets.jinja` already carried it at 5.3.3.

- **CSS only — do not load `bootstrap.bundle.js`.** Bootstrap's `data-bs-*`
  API is a second state owner for the modal, the tabs and the accordion, and
  `cf_ui_alpine.js` is already the first. Loading both would make
  `Alpine.store('cf').modal.open(id)` behave differently under this theme than
  under every other one, which is precisely the cross-theme guarantee the theme
  work exists to protect. The templates use Bootstrap's classes and markup
  structure and wire every piece of state through the existing Alpine
  components; the absence of `data-bs-` is asserted per component rather than
  left to prose.

- **The modal reveal rides on `d-block`, not on `.show` alone.** `.modal` is
  `display: none` and Bootstrap's `.show` only sets opacity — its own JS is
  what writes `style.display = "block"`. A theme that toggled just `.show`
  would change the class list and never become visible, so the E2E tier asserts
  visibility rather than classes. The backdrop is likewise a special case:
  Bootstrap appends one to `<body>` at z-index 1050, below the modal's 1055,
  and cf-ui has no JS to do that. It lives inside the modal with a negative
  z-index instead, which keeps it under the dialog rather than swallowing every
  click. Both halves — the dialog still takes clicks, the backdrop still closes
  — are covered by an E2E test.

- **The panel body carries no `.collapse`.** That class is `display: none`
  without `.show`, which would hide a server-open panel permanently once Alpine
  is off — exactly the bug #21 fixed. `x-show` owns display, seeded from
  `data-cf-open`. The navbar *does* use `.collapse`, where the pure-CSS
  `.collapse:not(.show)` / `.navbar-expand-lg .navbar-collapse` pair is the
  correct behavior with or without JS.

- Accessibility parity with Bulma and DaisyUI is enforced by the existing
  `tests/unit/test_accessibility.py`, which now parametrizes over three themes
  rather than two: dialog semantics and the `label` fallback, the tabs'
  server-rendered active state with roving `tabindex`, and the panel's
  `aria-expanded` / `aria-controls` toggle.

- Prop vocabulary is unchanged and still theme-agnostic. `type="danger"` maps to
  `alert-danger` / `bg-danger`, and `type="error"` maps there too, so a value
  written for DaisyUI keeps working.

### Added — real Tailwind build in CI (#17)

- **A CI job that builds the vendored plugin through the actual Tailwind CLI.**
  Nothing did before. The existing suite calls the plugin's exports directly, so
  every claim it makes about *Tailwind* is a proxy — and both defects fixed in
  #7 were invisible to it, surfacing only under a real build. The sharpest case
  is `assert.equal(cfUiAxes.__isOptionsFunction, true)`: it asserts cf-ui still
  sets a flag, not that Tailwind still reads it. Rename the marker in both the
  plugin and that assertion and the suite stays green while the CSS-first path
  silently stops accepting options, leaving only the default composition
  validated — which always passes.

  The new job compiles a bare `@plugin` and `@plugin { composition: console; }`,
  asserts the compiled CSS actually carries the axis rules, the
  `--color-primary` aliases and the `@media (color-gamut: p3)` layer (a build
  that succeeds and emits nothing is the other silent failure), and asserts an
  unknown composition exits non-zero — read from the process directly, since
  piping masks the status. Tailwind is pinned; a break on bump is the signal.

  Run it locally with `just test-tailwind`. It throws rather than skipping when
  the toolchain is absent, because a skip reads as a pass.

### Fixed — accessibility (#21)

Three gaps that predate 0.1.0 and were flagged during the #6 review, fixed
against both shipped themes before the theme-expansion epic copies the patterns
into three more.

- **The modal had no dialog semantics and no focus management.** It rendered a
  plain `<div>`: a screen reader had no way to know a dialog opened, and
  keyboard focus stayed behind it. It now carries `role="dialog"` and
  `aria-modal="true"`, is named by its header via `aria-labelledby` (or by a new
  `label` prop, defaulting to `"Dialog"`, when there is no header), moves focus
  into itself on open, returns focus to whatever opened it on close, traps `Tab`
  and `Shift+Tab` while open, and closes on `Escape`.

  It stays a `<div>` rather than becoming a native `<dialog>`. `showModal()`
  would give all of the above for free, but only where a theme's CSS is built
  around it — it would make `cfModal` branch per theme, and the identical
  cross-theme Alpine contract is what the theme work exists to protect. The
  whole implementation is in `cf_ui_alpine.js`, once, so a new theme inherits it
  by writing markup. See [`docs/accessibility.md`](docs/accessibility.md).

- **Tabs showed no active tab without JavaScript.** The active marker existed
  only as an Alpine binding, so a JS-less page rendered every tab identically —
  navigation worked (tabs are HTMX-driven), but nothing said which one you were
  on. `CfTabs` / `<c-cf.tabs>` now take an `active` prop and server-render the
  active class, `aria-selected`, `aria-controls`, and a roving `tabindex` from
  it. The Alpine binding stays on top: the server value is the initial state,
  not a replacement. Keyboard support follows the ARIA tabs pattern with manual
  activation — arrows move focus, `Enter`/`Space` activates — because automatic
  activation would fire an HTMX request on every arrow press.

- **`CfPanel`'s `open` prop was declared but never rendered.** An open panel
  still emitted `x-cloak`, so with Alpine off it was hidden permanently. The
  panel now renders its open state server-side, seeds Alpine from it rather than
  resetting to closed, and its toggle is a real `<button type="button">` with
  `aria-controls` and `aria-expanded`.

  **New prop:** `CfPanel` takes an `id` (default `"panel"`), used for
  `aria-controls="{id}-body"`. Two panels on one page need distinct `id`s or
  they will emit duplicate element ids.

- Tabs and Panel receive their server state through `data-` attributes read in
  `x-init`, never through an interpolated `x-data="cfTabs('{{ active }}')"`. The
  value is request-controlled, and a template engine escapes an attribute
  correctly but has no idea it is writing JavaScript source.

- `docs/accessibility.md` records the `<div>`-over-`<dialog>` decision and its
  reasoning, so it is not relitigated per theme.

### Changed — BREAKING (#20)

The axis layer stated four properties it did not enforce. Enforcing them is
breaking for anyone who was relying, knowingly or not, on the gaps.

- **Token *values* are now validated, not just token names.** A value containing
  `;`, `{`, `}`, `<`, `/*`, or `*/` raises `AxisConfigError`, and a non-string
  value is rejected outright. Values are interpolated straight into the
  `<style>` element `style_element()` injects, so a semicolon or brace closed
  the declaration and wrote rules the app never authored — `</style>` escaped
  the element entirely. This mattered most for the deployments cf-ui explicitly
  targets, where value sets come from a database column or an admin form rather
  than a hand-written literal. The plugin already rejected these; the two
  generators now agree, and a test asserts they reject the same inputs.
  **Migration:** none for hand-written value sets. If a value legitimately needs
  one of these characters, it is not an axis token.
- **The `--cf-spacing` → `--spacing` alias is gone.** `--color-primary*` is a
  name cf-ui owns in a Tailwind context; `--spacing` is the root of Tailwind
  v4's entire spacing scale, so `data-density` was silently rescaling every
  `p-4` and `gap-2` in the consuming app by ±20% — including for Bulma consumers
  using none of it. `--cf-spacing` is still emitted.
  **Migration:** to keep the old behavior, add `@theme { --spacing: var(--cf-spacing); }`.
- **Every exported generator validates by default**, on both sides of the
  language boundary. These were escape hatches that generated CSS with the gate
  switched off, contradicting the guarantee #7 shipped on — and `style_element`
  is the very sink the token-value gate above exists to protect, so it emitted
  an injection payload verbatim when called directly.
  - JavaScript: `buildAxisBase(sets, definition, { validate: false })`,
    `buildAxisCss(...)` — same opt-out.
  - Python: `render_axis_css(sets, banner=True, validate=True)`,
    `custom_axis_css(sets, banner=False, validate=True)`,
    `style_element(sets, validate=True)`.

  **Migration:** code passing invalid value sets to any of these now throws.
  That was already producing malformed CSS. The documented entry points
  (`CF_UI_AXIS_VALUES`, the FastAPI/Litestar `value_sets=` argument) route
  through `merge_value_sets` and are unaffected.

### Added
- **The wide-gamut lightness invariant is enforced (#20).** `p3_lightness_failures()`
  (Python) and `p3LightnessFailures()` (plugin) convert each sRGB base declaration
  to OKLab and compare it against the `oklch()` override, failing CI beyond 0.5
  percentage points. The contrast gate is computed against the sRGB base and
  cannot measure `oklch()`; "the p3 layer holds the same lightness" was the
  convention carrying that result to wide-gamut displays, held by hand. A typo
  or a monitor-driven tweak shipped below AA with every test green, invisible to
  anyone reviewing on an sRGB display.
- `cf_ui.axes.oklab_lightness()` / `oklch_lightness()`, and their plugin
  counterparts `oklabLightness()` / `oklchLightness()`
- `.gitattributes` pinning the generated axis artifacts to LF — `python -m
  cf_ui.axes` writes `newline="\n"`, so without it every regeneration left a
  phantom zero-line diff and "is the tree clean" meant nothing
- Tailwind plugin with build-time axis validation (#7): an unknown axis value now
  **fails the CSS build** instead of silently producing an unstyled element
- `static/cf_ui/cf_ui_tailwind_plugin.mjs` — vendored into the wheel, not published
  to npm, so its version can never skew from the definition it enforces. Imports
  nothing but Node builtins and exports Tailwind's `{ handler, config }` shape,
  usable via `@plugin` or a JS config
- `cf_ui.axes.axis_definition()` and `static/cf_ui/cf_ui_axes.json` — the axis
  definition as data, so the plugin can read it from inside a CSS build where
  Python is not. `python -m cf_ui.axes` now writes both generated files
- The `@media (color-gamut: p3)` layer is generated by the plugin from the same
  definition rather than kept in sync by hand
- Optional contrast report (`contrastReport: true`) over every accent × surface ×
  mode; warns rather than failing, so cf-ui does not decide when a consuming app
  may compile
- Consumer value sets accepted by the plugin with the same `extend` / `replace`
  semantics as `merge_value_sets` (#5)
- `tests/js/` — a `node --test` tier, run directly in CI and wrapped by pytest
- `docs/tailwind-plugin.md`; `just test-js` and `just axes`
- **DaisyUI theme (#6)** — all 14 components in both template sets
  (`jinja/daisy/*.jinja` and `cotton/_themes/daisy/*.html`), covered by the
  full three-tier suite including Playwright E2E in `js_on` and `js_off`
- `cf_ui/themes.py` — theme registry (`THEMES`, `COMPONENTS`, `resolve_theme`,
  `cotton_partial`, `tailwind_content_globs`); `CF_UI_THEME` is now validated
  by `CfUiConfig.ready()` instead of failing later as `TemplateDoesNotExist`
- django-cotton theme dispatch: `cotton/cf/<name>.html` is now a wrapper that
  declares `<c-vars>` and includes `cotton/_themes/<theme>/<name>.html` via the
  new `{% cf_ui_theme_path %}` tag. Consumer templates are unchanged —
  `<c-cf.card>` still resolves at the same path, and `COTTON_DIR` is still
  untouched (see #4)
- `docs/daisyui.md` — theme switch, the Tailwind content glob, and preflight
  coexistence while migrating off another framework
- `python -m cf_ui.themes` prints the absolute Tailwind content globs for the
  installed package, so consumers do not hand-write a site-packages path
- Theme composition axes (#5): five orthogonal style axes — accent, surface, form,
  density, type — each keyed on a data attribute and carrying a closed set of
  named values. `data-theme` remains the light/dark switch and is not an axis.
- `cf_ui/axes.py` — single source of truth for axis definitions, named
  compositions, value-set merging, CSS generation, and WCAG contrast checking
- `static/cf_ui/cf_ui_axes.css` — generated from `axes.py` via `python -m cf_ui.axes`,
  delivered by the existing asset tags; a unit test fails on drift
- `CF_UI_COMPOSITION`, `CF_UI_AXIS_VALUES`, `CF_UI_AXIS_VALUES_MODE` Django settings,
  validated at startup by `CfUiConfig.ready()`
- `{% cf_ui_root_attrs %}` template tag and `cf_ui_root_attrs()` Jinja macro —
  one setting in, five attributes out
- `composition=` / `value_sets=` / `value_sets_mode=` on both `install_cf_ui()`
  functions, registering the Jinja globals the macros delegate to
- `docs/theming.md` — axis reference, custom value sets, and the contrast requirement

### Changed
- E2E harness is parameterized by theme: `make_app(theme)` for the FastAPI
  gallery and `CF_UI_E2E_THEME` for the Django server. The DaisyUI E2E run
  reuses the Bulma consumer templates verbatim, which is what makes
  "switching themes needs no template edits" an executed claim rather than a
  documented one

### Technical Notes
- `axes.py` remains the single source of truth. The plugin holds no copy of the
  value sets, and a parity test compares both generators' output declaration by
  declaration — selectors, custom properties, values, and the p3 layer
- Token values containing `;`, `{`, `}`, or a comment delimiter are rejected by the
  plugin: they close their own declaration and write rules the app never authored
- Every DaisyUI variant class is written out in full
  (`{% if type == 'danger' %}alert-error{% endif %}`, never `alert-{{ type }}`)
  because Tailwind's scanner reads source text and cannot see a class assembled
  at render time. A test scans the DaisyUI templates for split class tokens
- The prop vocabulary is unchanged across themes: `type="danger"` still works,
  and the templates map it onto DaisyUI's `alert-error` / `progress-error`
- Alpine components are untouched — `cfModal`, `cfNavbar`, `cfPanel`, `cfTabs`
  and the `$cf` store are theme-independent; only the toggled class differs
  (`is-active` → `modal-open` / `tab-active`)
- Django rejects template variables beginning with an underscore, so the
  dispatch variable is `cf_ui_partial`, not `_cf_partial`
- Light and dark are declared independently per value, never derived by inversion;
  light is the unqualified selector, dark is `[data-theme="dark"][data-*="..."]`
- Base declarations are sRGB hex (what the contrast gate is computed against);
  wide-gamut chroma is layered behind `@media (color-gamut: p3)` — not
  `@supports (color: oklch(...))`, which is a no-op in every current browser
- Accent aliases to `--color-primary*` for Tailwind v4 interop. Density
  originally aliased `--cf-spacing` to `--spacing`; that was removed before
  release (see the breaking change above) and never shipped in a tagged version

## [0.1.1] — 2026-04-28

### Fixed
- **Consumer compatibility regression**: `CfUiConfig.ready()` no longer
  overrides `settings.COTTON_DIR`. The previous fix in 0.1.0 set
  `COTTON_DIR="cotton/bulma"` globally, which broke any consumer project
  whose own cotton templates lived at `templates/cotton/<their-app>/...`
  (every `<c-foo.bar>` lookup got rewritten to
  `cotton/bulma/foo/bar/index.html` and raised `TemplateDoesNotExist`).

### Changed
- cf-ui's cotton templates moved from `cotton/<theme>/cf/*.html` to
  `cotton/cf/*.html`. Theme variation will now happen inside the templates
  (or via `_themes/` partials) instead of at the directory level. With the
  default `COTTON_DIR="cotton"`, `<c-cf.foo>` continues to resolve and
  consumer cotton trees are no longer affected.

### Migration
- Most consumers: no change required. Removing any explicit
  `COTTON_DIR="cotton/bulma"` from `settings.py` (added as a workaround
  while 0.1.0 was broken) is recommended.
- If you imported `COTTON_TEMPLATES_DIR / "bulma"` directly via the escape
  hatch, switch to `COTTON_TEMPLATES_DIR / "cf"`.

## [0.1.0] — 2026-04-25

### Added
- Initial release: Bulma theme (Jinja2/JinjaX + django-cotton)
- 14 components: FormField, Select, Textarea, CheckboxGroup, Modal, Notification,
  Progress, Card, Table, Pagination, Panel, Navbar, Breadcrumb, Tabs
- Django AppConfig with auto-registration of COTTON_DIRS
- FastAPI `install_cf_ui()` with JinjaX `add_folder(prefix="Cf")` registration
- Litestar `install_cf_ui()` with Jinja2 template directory injection
- CDN asset tags: `{% cf_ui_head %}` / `{% cf_ui_body %}` (Django + Jinja2 macros)
- `cf_ui_alpine.js`: named Alpine components (cfModal, cfNavbar, cfPanel, cfTabs)
  and `$store.cf` global store (notify, modal.open/close via custom events)
- Three-tier test suite: unit (93 tests), integration (8 tests), E2E Playwright (17 tests, js_on + js_off)
- Stubs for Bootstrap, Foundation, Fomantic UI, DaisyUI themes

### Technical Notes
- django-cotton 2.x: uses `<c-vars>` (not `<c-props>`) for variable declarations
- JinjaX 0.41+: uses `add_folder()` (not `add_path()`), `class` is reserved — use `extra_class`
- Alpine modal control uses `cf-modal-open`/`cf-modal-close` custom events (not `_x_dataStack`)
