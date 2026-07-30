# Bootstrap theme

Bootstrap is the one theme where cf-ui deliberately does **not** follow the
framework's own installation instructions. Bootstrap tells you to include
`bootstrap.bundle.min.js`. cf-ui ships CSS only and drives every interactive
component from Alpine.

This file is the decision record for that, because it is a question a consumer
will reasonably ask and because it is not obvious from the templates.

## Switching to it

```python
# settings.py  (Django)
CF_UI_THEME = "bootstrap"
```

```python
# FastAPI
from cf_ui.fastapi import install_cf_ui
install_cf_ui(catalog, theme="bootstrap")

# Litestar
from cf_ui.litestar import install_cf_ui
install_cf_ui(template_config, theme="bootstrap")
```

`cf_ui_head()` emits the pinned `bootstrap.min.css`. `cf_ui_body()` emits
`cf_ui_alpine.js` and Alpine. Neither emits `bootstrap.bundle.min.js`, and there
is no setting that makes them.

## The decision

**CSS only. Alpine owns behaviour. `bootstrap.bundle.min.js` is not shipped.**

Three reasons, in the order they mattered:

**One behavioural contract across every theme.** `Alpine.store('cf').modal.open(id)`
opens a modal identically under Bulma, DaisyUI, Bootstrap, Foundation and
Fomantic. `cf_ui_alpine.js` owns modal focus management, tab switching, panel
state, and the navbar toggle for all of them. Loading Bootstrap's JS for one
theme would make Bootstrap a second state owner for components cf-ui already
drives, and would make "switch `CF_UI_THEME`" stop being a config change.

**Bootstrap itself sanctions this.** Its docs are explicit that its JS is
incompatible with frameworks that own the DOM, and direct you to a
framework-native implementation instead. Alpine is a weaker case than React or
Vue — it has no virtual DOM to reconcile against — but the blessing is the same
one, and cf-ui is exercising it rather than working around it.

**The no-JS tier is a stated guarantee here, and is not one in Bootstrap.**
Bootstrap ships no fallback for a JS-disabled page. cf-ui's E2E suite is
parameterized over `js_on` / `js_off` and asserts components stay usable in
both. That is a property worth keeping, and it constrains the markup — the
navbar collapse, for instance, is plain CSS (`.collapse:not(.show)` plus
`.navbar-expand-lg .navbar-collapse`), so only the toggle needs Alpine at all.

### What this costs

Bootstrap 5.3.3 ships **12** JS-driven components: `alert`, `button`,
`carousel`, `collapse`, `dropdown`, `modal`, `offcanvas`, `popover`,
`scrollspy`, `tab`, `toast`, `tooltip`. (`base-component.js` is the shared base
class, not a component.)

cf-ui's 14 components overlap four of those plugins:

| cf-ui component | Bootstrap plugin it replaces | Driven by |
|---|---|---|
| `CfModal` / `<c-cf.modal>` | Modal | `cfModal` — focus in/out, `Escape`, tab trap |
| `CfTabs` / `<c-cf.tabs>` | Tab | `cfTabs` — roving tabindex, manual activation |
| `CfPanel` / `<c-cf.panel>` | Collapse | `cfPanel` |
| `CfNavbar` / `<c-cf.navbar>` | Collapse | `cfNavbar` |
| `CfNotification` / `<c-cf.notification>` | Alert (dismiss) | inline Alpine |

The other eight — `button` (toggle), `carousel`, `dropdown`, `offcanvas`,
`popover`, `scrollspy`, `toast`, `tooltip` — cf-ui does not wrap at all. See
below.

## Using a Bootstrap component cf-ui does not ship

You have three options, in descending order of how much they will hurt.

**Write it with Alpine.** For `dropdown`, `toast` and `offcanvas` this is a
handful of lines and stays consistent with everything else on the page. It is
also what cf-ui itself did.

**Load Bootstrap's JS anyway, and keep it away from cf-ui components.** This
works, and nothing in cf-ui prevents it. The rule is absolute:

> **Never put a `data-bs-*` attribute on a cf-ui component.**

Bootstrap's JS binds by `data-bs-toggle` / `data-bs-target` and by class. Put
`data-bs-toggle="modal"` on a `<c-cf.modal>` trigger and both Bootstrap and
Alpine will manage the same dialog — two owners of `.show`, two focus policies,
and a component whose behaviour depends on script load order. The failure is
intermittent, which is the worst kind.

If you do load it, prefer the individual plugin over the bundle so it is
obvious what is active: `bootstrap.esm.js` exports each plugin separately, and
`popover`/`tooltip` are the only two that need Popper.

**Use a different component library for that one widget.** Perfectly
reasonable. cf-ui's components carry a `cf.` / `Cf` namespace precisely so they
can coexist with anything else in the same template.

### Considered and deferred: a behaviour driver

The obvious abstraction is a per-theme behaviour driver — a facade over
"open a modal", "switch a tab", so a theme could swap Alpine for the framework's
native JS without changing a template. It would make this whole page a
configuration choice instead of a decision.

It is deferred, not rejected. It is an abstraction for a problem no consumer has
reported, and the strongest reason to build it — Bootstrap 6 — has an API that
does not exist yet, so it would have to be designed against a guess. Revisit it
at the v6 rework (see below), when there is something concrete to design
against.

## Bootstrap 6

The pin is `5.3.3`, and `tests/unit/test_bootstrap_version_pin.py` fails the
moment it leaves the `5.x` line. That is deliberate: a promise to watch a
dependency does not survive, and a red test does. The failure message is the
checklist.

The short version, verified against `v6-dev` directly rather than from release
notes — several secondary sources claim v6 already adopted native `<dialog>`
citing twbs#41751, which is **closed and was never merged**:

- **`_modal.scss` is gone.** v6 has `_dialog.scss`, defining `.dialog`,
  `.dialog-header`, `.dialog-body`, `.dialog-footer`, `.dialog-title`,
  `.dialog-scrollable`, `.dialog-fullscreen`, `.dialog-nonmodal` and siblings.
  No `.modal*` selector survives.
- **`modal.js` is gone**, replaced by `dialog.ts` / `dialog-base.ts` built on
  `HTMLDialogElement.showModal()`.
- **The JS surface is growing**, not shrinking: `combobox`, `datepicker`,
  `otp-input`, `chips`, `strength`, `drawer`, `menu`, `range` are all new.

The consequence worth internalising: cf-ui's bootstrap modal templates carry
eight `modal-*` class references each, so **they break at v6 on the CSS alone,
whatever is decided about JS.** The markup needs rework regardless, which is
exactly when re-pricing the JS decision is cheapest. That is why this page
defers the question instead of pre-solving it.

As of 2026-07-29 v6 is at `6.0.0-alpha1` and maintainers describe it as not
arriving soon.

## What stays the same

Everything a consumer touches. Component names are theme-agnostic (`CfCard`,
`<c-cf.card>`), prop vocabulary is theme-agnostic (`type="danger"` maps to
`alert-danger` inside the partial), and the Alpine store API is identical. The
Tailwind content glob discussion in [docs/daisyui.md](daisyui.md) does **not**
apply — Bootstrap ships prebuilt CSS, so nothing gets tree-shaken.

Accessibility guarantees and where they live are in
[docs/accessibility.md](accessibility.md). They are the same for every theme by
construction; that is the point of keeping behaviour in one file.
