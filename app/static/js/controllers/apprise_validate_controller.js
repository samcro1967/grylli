import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
    static targets = ["label", "url", "submit"];

    connect() {
        this.update();
        this.labelTarget.addEventListener("input", this.update.bind(this));
        this.urlTarget.addEventListener("input", this.update.bind(this));
    }

    update() {
        const valid = this.labelTarget.value.trim() !== "" && this.urlTarget.value.trim() !== "";
        this.submitTarget.disabled = !valid;
        this.submitTarget.classList.toggle("bg-green-600", valid);
        this.submitTarget.classList.toggle("bg-red-500", !valid);
    }
}
