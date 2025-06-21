// app/static/js/controllers/collapse_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
    static targets = ["content", "icon"];

    connect() {
        this._setInitialState();
    }

    toggle() {
        this.contentTargets.forEach((el, index) => {
            const isOpen = el.style.display === "" || el.style.display === "block";
            el.style.display = isOpen ? "none" : "block";
            if (this.hasIconTarget) {
                this.iconTargets[index].style.transform = isOpen ? "rotate(0deg)" : "rotate(180deg)";
            }
        });
    }

    _setInitialState() {
        this.contentTargets.forEach((el, index) => {
            el.style.display = "block";
            if (this.hasIconTarget) {
                this.iconTargets[index].style.transform = "rotate(180deg)";
            }
        });
    }
}
