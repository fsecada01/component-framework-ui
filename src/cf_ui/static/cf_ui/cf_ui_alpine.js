/**
 * cf_ui_alpine.js — Alpine.js named components and $cf global store.
 * Must be loaded BEFORE Alpine CDN (both with defer — DOM order guarantees cf_ui_alpine.js runs first).
 * Requires Alpine.js 3.x.
 */
document.addEventListener('alpine:init', () => {
    // ── Named components ──────────────────────────────────────────────────────

    Alpine.data('cfModal', () => ({
        open: false,
        toggle() {
            this.open = !this.open;
        },
        close() {
            this.open = false;
        },
    }));

    Alpine.data('cfNavbar', () => ({
        menuOpen: false,
    }));

    Alpine.data('cfPanel', () => ({
        open: false,
    }));

    Alpine.data('cfTabs', () => ({
        active: null,
        setActive(id) {
            this.active = id;
        },
    }));

    // ── $cf global store ──────────────────────────────────────────────────────

    Alpine.store('cf', {
        _notifications: [],

        notify(message, type = 'info', duration = 4000) {
            const id = Date.now();
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
                const el = document.getElementById(id);
                if (el && el._x_dataStack && el._x_dataStack.length > 0) {
                    el._x_dataStack[0].open = true;
                }
            },
            close(id) {
                const el = document.getElementById(id);
                if (el && el._x_dataStack && el._x_dataStack.length > 0) {
                    el._x_dataStack[0].open = false;
                }
            },
        },
    });
});
