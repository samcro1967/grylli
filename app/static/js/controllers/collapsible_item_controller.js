// app/static/js/controllers/collapsible_item_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
    static targets = ["content", "icon"];
    static values = {
        open: Boolean
    };

    connect() {
        this._update();
    }

    toggle() {
        this.openValue = !this.openValue;
        this._update();
    }

    _update() {
        if (this.hasContentTarget) {
            this.contentTarget.classList.toggle("hidden", !this.openValue);
        }

        if (this.hasIconTarget) {
            this.iconTarget.classList.toggle("rotate-90", this.openValue);
        }
    }
}
