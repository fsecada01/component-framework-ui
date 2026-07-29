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

New state crosses into Alpine through `data-` attributes, read in an `x-init`
hook — `data-cf-active` → `initTabs()`, `data-cf-open` → `initPanel()` — rather
than through an interpolated `x-data="cfTabs('{{ active }}')"`.

The value is request-controlled. A template engine escapes an *attribute*
correctly; it has no idea it is writing JavaScript source, so a single
apostrophe in `active` breaks out of the expression. The data-attribute route
has no such seam.

---

## Testing

Split deliberately, because #21 exists as a ticket largely because the earlier
tests could not have caught what they claimed to:

* `tests/unit/test_accessibility.py` — claims that *are* markup: a role, an
  `aria-*` value, a server-rendered class. All four template sets, every case.
* `tests/e2e/` — claims that are behavior: where focus lands after open, where
  it lands after close, that `Tab` cannot leave the dialog. Parameterized over
  `js_on` / `js_off`.

`expect(role_is_dialog)` proves nothing about focus, and
`expect(tab).to_be_attached()` passes against markup nobody can use. Assert the
behavior.
