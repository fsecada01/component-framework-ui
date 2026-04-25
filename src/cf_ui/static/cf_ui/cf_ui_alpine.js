/**
 * cf_ui_alpine.js — Alpine.js named components and $cf global store.
 * Must be loaded BEFORE Alpine CDN (both with defer — DOM order guarantees cf_ui_alpine.js runs first).
 * Requires Alpine.js 3.x.
 */

let _notifId = 0;

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
        initModal() {
            this.$el.addEventListener('cf-modal-open', () => { this.open = true; });
            this.$el.addEventListener('cf-modal-close', () => { this.open = false; });
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
        toggle() {
            this.open = !this.open;
        },
    }));

    Alpine.data('cfTabs', () => ({
        active: null,
        setActive(id) {
            this.active = id;
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
