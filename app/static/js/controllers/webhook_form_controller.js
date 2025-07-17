// app/static/js/controllers/webhook_form_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
    static targets = ["label", "endpoint", "submit"];

    connect() {
        this.updateButtonState();
    }

    validate() {
        this.updateButtonState();
    }

    updateButtonState() {
        const label = this.labelTarget.value.trim();
        const endpoint = this.endpointTarget.value.trim();
        const isValid = label !== "" && endpoint !== "";

        this.submitTarget.disabled = !isValid;
        this.submitTarget.classList.toggle("bg-green-600", isValid);
        this.submitTarget.classList.toggle("bg-red-500", !isValid);
    }
}
