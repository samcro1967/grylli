// app/static/js/controllers/collapse_controller.js

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
    static targets = ["content", "icon"];
    static values = { id: String };

    connect() {
        this._setInitialState();

        // Add an event listener that runs after HTMX swaps content
        document.body.addEventListener("htmx:afterSwap", () => {
            // Ensure we only apply the state to the correct section after HTMX swaps
            if (this._shouldApplyState()) {
                this._setInitialState();
            }
        });
    }

    toggle() {
        const isCurrentlyOpen = this._isOpen();

        this.contentTargets.forEach((el, index) => {
            if (isCurrentlyOpen) {
                el.classList.add("hidden");
            } else {
                el.classList.remove("hidden");
            }
            if (this.hasIconTarget) {
                this.iconTargets[index].classList.toggle("rotate-180", !isCurrentlyOpen);
                this.iconTargets[index].classList.toggle("rotate-0", isCurrentlyOpen);
            }
        });

        this._saveState(!isCurrentlyOpen);
    }

    _setInitialState() {
        const isOpen = this._getState();

        this.contentTargets.forEach((el, index) => {
            if (isOpen) {
                el.classList.remove("hidden");
            } else {
                el.classList.add("hidden");
            }
            if (this.hasIconTarget) {
                this.iconTargets[index].classList.toggle("rotate-180", isOpen);
                this.iconTargets[index].classList.toggle("rotate-0", !isOpen);
            }
        });
    }

    _getState() {
        const stored = localStorage.getItem("__GrylliSidebar");
        if (!stored) return true; // default to expanded
        const parsed = JSON.parse(stored);
        return parsed[this.idValue] !== false; // treat missing or true as open
    }

    _saveState(isOpen) {
        const stored = localStorage.getItem("__GrylliSidebar");
        const parsed = stored ? JSON.parse(stored) : {};
        parsed[this.idValue] = isOpen;
        localStorage.setItem("__GrylliSidebar", JSON.stringify(parsed));
    }

    _isOpen() {
        return this.contentTargets.length && !this.contentTargets[0].classList.contains("hidden");
    }

    // Helper to determine if the state should be applied after HTMX content swap
    _shouldApplyState() {
        // Only apply to shared_nav sections (if needed)
        return this.idValue === "reminders" || this.idValue === "notifications";
    }
}
