/**
 * cf_ui_alpine.js — Alpine.js named components and $cf global store.
 * Must be loaded BEFORE Alpine CDN (both with defer — DOM order guarantees cf_ui_alpine.js runs first).
 * Requires Alpine.js 3.x.
 */

let _notifId = 0;

// Tabbable elements. `[tabindex="-1"]` is excluded on purpose: it is
// programmatically focusable but not part of the tab sequence, so a focus trap
// that included it would wrap in the wrong place.
const CF_FOCUSABLE = [
    'a[href]',
    'area[href]',
    'button:not([disabled])',
    'input:not([disabled]):not([type="hidden"])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    'iframe',
    'audio[controls]',
    'video[controls]',
    '[contenteditable]:not([contenteditable="false"])',
    '[tabindex]:not([tabindex="-1"])',
].join(',');

/** Tabbable descendants of `root` that are actually rendered. */
function cfFocusable(root) {
    return Array.from(root.querySelectorAll(CF_FOCUSABLE)).filter(
        (el) => el.getClientRects().length > 0
    );
}

// Frames `_focusFirst` will keep retrying for before giving up. ~10 frames is
// well past any reveal transition and still bounded, so a dialog that never
// becomes visible cannot spin forever.
const CF_FOCUS_ATTEMPTS = 10;

document.addEventListener('alpine:init', () => {
    // ── Named components ──────────────────────────────────────────────────────

    // Deliberately driven from a <div>, not a native <dialog>. See
    // docs/accessibility.md — one Alpine implementation covers every theme,
    // where showModal() would make this component branch per theme. Everything
    // <dialog> would have given for free is implemented below, once.
    Alpine.data('cfModal', () => ({
        open: false,
        // Where focus returns on close. Captured when the dialog opens rather
        // than declared by the template, so any trigger works — a button, a
        // link, a keyboard shortcut — without the markup knowing about it.
        _returnFocusTo: null,

        toggle() {
            if (this.open) {
                this.close();
            } else {
                this.show();
            }
        },

        show() {
            if (this.open) return;
            this._returnFocusTo = document.activeElement;
            this.open = true;
        },

        close() {
            if (!this.open) return;
            this.open = false;
            const target = this._returnFocusTo;
            this._returnFocusTo = null;
            if (target && typeof target.focus === 'function' && target.isConnected) {
                target.focus();
            }
        },

        _focusFirst(attempt = 0) {
            // A retry scheduled before the dialog was closed again must not
            // yank focus back into it.
            if (!this.open) return;

            const targets = cfFocusable(this.$el);
            // A dialog with nothing tabbable in it still has to take focus, or
            // the reader stays behind it and the trap has nothing to hold.
            if (!targets.length) this.$el.setAttribute('tabindex', '-1');
            (targets[0] || this.$el).focus();

            // `focus()` on an element that is not rendered yet is a silent
            // no-op — on both the child and the $el fallback. Nothing
            // guarantees the class that reveals the dialog has been committed
            // by the time this runs: Alpine does not order the `:class` effect
            // against a $watch's $nextTick, and a theme may reveal behind a
            // transition. So verify and retry per frame rather than trusting
            // one flush's ordering. CI caught exactly this; it passed locally
            // every time.
            if (!this.$el.contains(document.activeElement) && attempt < CF_FOCUS_ATTEMPTS) {
                requestAnimationFrame(() => this._focusFirst(attempt + 1));
            }
        },

        _trapTab(event) {
            const targets = cfFocusable(this.$el);
            if (!targets.length) {
                event.preventDefault();
                return;
            }
            const first = targets[0];
            const last = targets[targets.length - 1];
            const inside = this.$el.contains(document.activeElement);
            if (event.shiftKey) {
                if (!inside || document.activeElement === first) {
                    event.preventDefault();
                    last.focus();
                }
            } else if (!inside || document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        },

        initModal() {
            this.$el.addEventListener('cf-modal-open', () => this.show());
            this.$el.addEventListener('cf-modal-close', () => this.close());
            this.$el.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') {
                    event.preventDefault();
                    this.close();
                } else if (event.key === 'Tab') {
                    this._trapTab(event);
                }
            });
            // Watched rather than folded into show(), so a consumer that sets
            // `open` directly still gets focus management.
            this.$watch('open', (isOpen) => {
                if (isOpen) this.$nextTick(() => this._focusFirst());
            });
        },
    }));

    Alpine.data('cfNavbar', () => ({
        menuOpen: false,
        toggle() {
            this.menuOpen = !this.menuOpen;
        },
    }));

    Alpine.data('cfPanel', () => ({
        open: false,
        initPanel() {
            // Seeded from the server-rendered state so the Alpine binding
            // continues the initial value rather than resetting it to closed.
            this.open = this.$el.dataset.cfOpen === 'true';
        },
        toggle() {
            this.open = !this.open;
        },
    }));

    Alpine.data('cfTabs', () => ({
        active: null,

        initTabs() {
            // Read from a data attribute rather than an interpolated
            // `x-data="cfTabs('{{ active }}')"`. The value is request-controlled,
            // and a template engine escapes an attribute correctly but has no
            // way to escape JavaScript source text.
            this.active = this.$el.dataset.cfActive || null;
        },

        setActive(id) {
            this.active = id;
        },

        _tabs() {
            return Array.from(this.$el.querySelectorAll('[role="tab"]'));
        },

        // Roving tabindex. With no tab selected the first one holds the 0 —
        // otherwise the whole widget drops out of the tab order, since these
        // anchors carry no href and tabindex is all that makes them focusable.
        tabIndexFor(id) {
            if (this.active) return this.active === id ? 0 : -1;
            const tabs = this._tabs();
            return tabs.length && tabs[0].dataset.cfTab === id ? 0 : -1;
        },

        // Manual activation: arrows move focus, Enter/Space activates. Automatic
        // activation would fire an HTMX request on every arrow press.
        onKeydown(event) {
            const tabs = this._tabs();
            if (!tabs.length) return;
            const current = tabs.indexOf(document.activeElement);
            let next;
            switch (event.key) {
                case 'ArrowRight':
                case 'ArrowDown':
                    next = tabs[(current + 1) % tabs.length];
                    break;
                case 'ArrowLeft':
                case 'ArrowUp':
                    next = tabs[(current - 1 + tabs.length) % tabs.length];
                    break;
                case 'Home':
                    next = tabs[0];
                    break;
                case 'End':
                    next = tabs[tabs.length - 1];
                    break;
                case 'Enter':
                case ' ':
                    if (current < 0) return;
                    event.preventDefault();
                    tabs[current].click();
                    return;
                default:
                    return;
            }
            event.preventDefault();
            (current < 0 ? tabs[0] : next).focus();
        },
    }));

    // ── $cf global store ──────────────────────────────────────────────────────

    Alpine.store('cf', {
        // Dismissed entries set visible: false but are not pruned.
        // Templates are responsible for filtering: $store.cf._notifications.filter(n => n.visible)
        _notifications: [],

        notify(message, type = 'info', duration = 4000) {
            const id = ++_notifId;
            this._notifications.push({ id, message, type, visible: true });
            if (duration > 0) {
                setTimeout(() => this.dismiss(id), duration);
            }
        },

        dismiss(id) {
            const n = this._notifications.find((n) => n.id === id);
            if (n) n.visible = false;
        },

        modal: {
            open(id) {
                document.getElementById(id)?.dispatchEvent(
                    new CustomEvent('cf-modal-open', { bubbles: false })
                );
            },
            close(id) {
                document.getElementById(id)?.dispatchEvent(
                    new CustomEvent('cf-modal-close', { bubbles: false })
                );
            },
        },
    });
});
