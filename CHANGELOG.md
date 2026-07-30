# Changelog

## [Unreleased]

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
  escaping is a separate guarantee, and `install_cf_ui` still leaves JinjaX's
  `autoescape` off, so a double quote in `tab.id` can break out of
  `data-cf-tab` itself under FastAPI/Litestar. Django/cotton is unaffected.
  Tracked as #36, and called out in `docs/accessibility.md` with a workaround
  in the meantime.

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
