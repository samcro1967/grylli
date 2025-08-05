// ---------------------------------------------------------------------
// profile_dropdown_controller.js
// app/static/js/controllers/profile_dropdown_controller.js
// Stimulus controller for profile dropdown behavior.
// ---------------------------------------------------------------------

import { Controller } from "../vendor/stimulus.js";

export default class extends Controller {
    static targets = ["button", "menu", "container"];

    connect() {
        document.addEventListener("click", this._outsideClick);
    }

    disconnect() {
        document.removeEventListener("click", this._outsideClick);
    }

    toggle(event) {
        event.stopPropagation();
        const isOpen = this.menuTarget.classList.toggle("hidden") === false;
        this.buttonTarget.setAttribute("aria-expanded", isOpen);
    }

    close() {
        this.menuTarget.classList.add("hidden");
        this.buttonTarget.setAttribute("aria-expanded", "false");
    }

    _outsideClick = (event) => {
        if (!this.containerTarget.contains(event.target)) {
            this.close();
        }
    };
}
