// app/static/js/controllers/apprise_form_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["label", "url", "submit"];

  connect() {
    this.updateButtonState();
    this.labelTarget.addEventListener("input", () => this.updateButtonState());
    this.urlTarget.addEventListener("input", () => this.updateButtonState());
  }

  updateButtonState() {
    const valid = this.labelTarget.value.trim() !== "" && this.urlTarget.value.trim() !== "";
    this.submitTarget.disabled = !valid;
    this.submitTarget.classList.toggle("bg-green-600", valid);
    this.submitTarget.classList.toggle("bg-red-500", !valid);
  }
}
