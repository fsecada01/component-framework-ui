# Accessibility

What cf-ui guarantees about its interactive components, and — more usefully —
*where* those guarantees live, so a new theme inherits them instead of
reimplementing them.

The rule: **behavior is in `cf_ui_alpine.js`, state is in the template.** A
theme partial decides which classes express "selected" or "open". It never
decides what happens when you press `Tab`.

---

## Modal

### It is a `<div>`, on purpose

DaisyUI's canonical modal is a native `<dialog>`, and `showModal()` would hand
us focus trapping, `Escape`, the top layer, and the backdrop for free. cf-ui
uses a `<div>` with `role="dialog"` anyway.

The reason is not that `<dialog>` is worse — it is that Bulma has no `<dialog>`
convention, and the three themes in the expansion epic will not agree either.
Adopting it would make `cfModal` branch per theme, and the identical
cross-theme Alpine contract is exactly what the theme work protects. One
implementation covers every theme, present and future; that is the same trade
the composition axes make.

So everything `<dialog>` would have provided is implemented once, in
`cf_ui_alpine.js`:

| Guarantee | Where |
|---|---|
| `role="dialog"`, `aria-modal="true"` | theme partial (static markup) |
| Focus moves into the dialog on open | `cfModal.$watch('open')` → `_focusFirst()` |
| Focus returns to the trigger on close | `cfModal.close()` |
| Focus cannot leave while open | `cfModal._trapTab()` |
| `Escape` closes | `initModal()` keydown handler |

The trigger is **captured**, not declared: `show()` records
`document.activeElement`. Any opener works — a button, a link, a keyboard
shortcut, `Alpine.store('cf').modal.open(id)` — and no template has to name it.

#### Why `_focusFirst()` retries

`focus()` on an element that is not rendered yet is a silent no-op — on the
first tabbable child *and* on the `$el` fallback. So focus can only be taken
once the class that reveals the dialog has actually been committed, and nothing
guarantees that has happened by the time the watcher's `$nextTick` runs: Alpine
does not order the `:class` effect against it, and a theme is free to reveal
behind a transition. `_focusFirst()` therefore verifies the result and retries
per animation frame, bounded by `CF_FOCUS_ATTEMPTS`, rather than trusting one
flush's ordering. A retry that finds the dialog closed again bails out instead
of yanking focus back in.

This was not theoretical: it passed locally every run and failed on CI. The
regression test (`test_modal_takes_focus_even_when_the_reveal_is_late`) pins the
dialog hidden with a rule that outranks the reveal class, opens it, and lifts
the rule a couple of frames later — the race made deterministic.

### Labelling, and the `label` fallback

A dialog needs an accessible name. cf-ui picks one of two, never both:

* **With a header** — `aria-labelledby="{id}-title"`, pointing at the element
  that renders the header slot.
* **Without a header** — `aria-label="{label}"`, where `label` is a prop that
  defaults to `"Dialog"`.

An `aria-labelledby` aimed at an empty element is worse than no labelling: the
name resolves to the empty string and the reader announces nothing. That is why
the fallback exists and why the two are mutually exclusive.

```html
<!-- named by its header -->
<c-cf.modal id="confirm">
  <c-slot name="header">Delete this file?</c-slot>
  This cannot be undone.
</c-cf.modal>

<!-- no header: name it explicitly -->
<c-cf.modal id="prefs" label="Preferences">…</c-cf.modal>
```

```python
catalog.render("Cf:Modal", id="prefs", label="Preferences")
```

---

## Tabs

`active` is a **server-rendered** prop, not just an Alpine variable. Without it
— which is how cf-ui shipped through 0.1.x — a JS-less page rendered every tab
identically: navigation still worked (tabs are HTMX-driven), but nothing told
you which one you were on.

```html
<c-cf.tabs :tabs="tabs" active="overview" hx_target="tab-content" />
```

```python
catalog.render("Cf:Tabs", tabs=tabs, active="overview", hx_target="tab-content")
```

Server-rendered from that one prop: the theme's active class, `aria-selected`,
`aria-controls`, and the roving `tabindex`. The Alpine binding stays on top of
all four — the server value is the *initial* state, not a replacement for
client-side switching.

### Keyboard

Roving tabindex, **manual activation**: exactly one tab is in the page's tab
order; arrows move focus between tabs; `Enter` / `Space` activates. Automatic
activation (arrow = select) would fire an HTMX request on every arrow press.

| Key | Effect |
|---|---|
| `←` `→` `↑` `↓` | Move focus, wrapping at both ends |
| `Home` / `End` | First / last tab |
| `Enter` / `Space` | Activate the focused tab |

With no `active` prop, the **first** tab holds `tabindex="0"`. It has to: these
anchors carry no `href`, so `tabindex` is the only thing making them focusable
at all, and a widget where every tab is `-1` is unreachable by keyboard.

---

## Panel

`open` is server-rendered too. An open panel emits no `x-cloak`, so it is
readable with Alpine off; `initPanel()` then seeds Alpine from the same state
rather than resetting to closed.

The toggle is a real `<button type="button">` carrying `aria-controls` and a
server-rendered `aria-expanded`, with `:aria-expanded="open"` layered on top.
`aria-controls` points at `{id}-body` — which is why `CfPanel` takes an `id`,
and why two panels on one page need distinct ones.

A **closed** panel still cannot be opened without JS. Making that work needs
`<details>`/`<summary>`, which is a different component shape; it is tracked
separately rather than smuggled in here.

---

## Passing state into Alpine

**No template interpolation inside an attribute Alpine evaluates.** Not in
`x-data`, not in `x-init`, not in a `:binding`, not in an `@handler`. That is
the whole rule, and `tests/unit/test_alpine_expression_safety.py` enforces it
over every template in the package.

Initial state crosses in through `data-` attributes read in an `x-init` hook —
`data-cf-active` → `initTabs()`, `data-cf-open` → `initPanel()` — rather than
through an interpolated `x-data="cfTabs('{{ active }}')"`.

Per-item values do the same thing, one level down. Each tab carries
`data-cf-tab="{{ tab.id }}"`, and every binding on it reads that back:

```html
:aria-selected="active === $el.dataset.cfTab"
:tabindex="tabIndexFor($el.dataset.cfTab)"
@click.prevent="setActive($el.dataset.cfTab)"
```

not:

```html
:tabindex="tabIndexFor('{{ tab.id }}')"   <!-- #32 -->
```

**Escaping cannot fix an interpolated expression.** The template engine escapes
an *attribute* correctly, but it has no idea it is writing JavaScript source,
and the escaping is gone before Alpine ever sees the value: the HTML parser
decodes `&#x27;` back to `'` while building the DOM, and Alpine reads the
decoded attribute. A quote-bearing `tab.id` therefore closes its string literal
and runs, on page load, with no user interaction — which is exactly what #32
was. A `data-` attribute has no such seam: its value is never parsed as source,
so the worst a hostile value can do there is be a wrong string.

Attribute escaping is a separate guarantee, and cf-ui now makes it on both
paths. Django/cotton always had it — Django autoescapes by default. On the
Jinja side the guarantee lives **in the template files themselves**: every
cf-ui component wraps its body in `{% autoescape true %}`, so a `tab.id`
carrying a double quote is escaped whatever the surrounding environment is
configured to do — on a bare `jinjax.Catalog()` (whose environment does not
autoescape), on Litestar's plain-Jinja path, and for a consumer who registers
the templates with `add_folder` and never calls `install_cf_ui` at all. Until
#36 that value could break out of `data-cf-tab` itself and add attributes of
its own.

The installers never touch the environment's `autoescape` — the app's policy,
`select_autoescape` callables included, is the app's. That is not incidental:
an environment-level fix was tried first and failed three ways. It trampled
caller policies; it was order-dependent, because `autoescape` is read at
compile time and JinjaX caches compiled components; and respecting a truthy
policy instead reopened the hole for `select_autoescape(["html"])`, which
answers `False` for `.jinja` files. In-template blocks have no ordering, no
policy to fight, and cover consumers the installers never see.
`tests/unit/test_autoescape.py` guards the block's presence and placement in
every template so a new theme cannot ship without it, and
`tests/integration/test_jinja_autoescape.py` proves the behaviour against a
bare catalog. A prop that deliberately carries real markup must be passed as
`markupsafe.Markup`; slot content is unaffected (JinjaX hands it over as
`Markup` already).

If a binding needs a value the server knows, the answer is always another
`data-` attribute on the element carrying the binding — never a wider
expression. `$el.dataset.*` resolves against the element the directive sits on,
so an element that reads `$el.dataset.cfTab` has to carry `data-cf-tab` itself;
reaching into a child or parent instead would put theme-specific DOM structure
back into `cf_ui_alpine.js`, which is the split this package exists to keep.

---

## Testing

Split deliberately, because #21 exists as a ticket largely because the earlier
tests could not have caught what they claimed to:

* `tests/unit/test_accessibility.py` — claims that *are* markup: a role, an
  `aria-*` value, a server-rendered class. All four template sets, every case.
* `tests/unit/test_alpine_expression_safety.py` — the rule above, as a guard
  over the whole template tree rather than a per-theme check, so the next theme
  cannot reintroduce an interpolated expression by copying the last one.
* `tests/e2e/` — claims that are behavior: where focus lands after open, where
  it lands after close, that `Tab` cannot leave the dialog. Parameterized over
  `js_on` / `js_off`.

`tests/e2e/test_alpine_injection.py` is in that last group for a reason worth
naming: the unit tier can assert a rendered attribute holds no splice point, but
only a browser can show what happens when it does — the decode-then-evaluate
sequence that makes the bug possible needs a real HTML parser and a real Alpine.
It asserts the payload did not run **and** that the bindings did evaluate; a fix
that made Alpine throw would pass the first half while leaving tabs dead.

`expect(role_is_dialog)` proves nothing about focus, and
`expect(tab).to_be_attached()` passes against markup nobody can use. Assert the
behavior.

One caveat that cost a CI cycle: a focus assertion has to **wait**, not sample.
`document.activeElement` read once, immediately after the reveal class lands,
races `_focusFirst()`'s retry loop — a fast machine wins it every time and a
loaded CI runner does not. Use `_wait_for_modal_focus(page)`, and press keys
that the dialog handles only after it returns.
