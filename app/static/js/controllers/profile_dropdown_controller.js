// app/static/js/controllers/profile_dropdown_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

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

    _outsideClick = (event) => {
        if (!this.containerTarget.contains(event.target)) {
            this.menuTarget.classList.add("hidden");
            this.buttonTarget.setAttribute("aria-expanded", "false");
        }
    };
}
