// static/js/controllers/forgot_username_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["email", "submit"];

  connect() {
    this.updateState();
  }

  initialize() {
    this.validateEmail = this.validateEmail.bind(this);
    this.updateState = this.updateState.bind(this);
  }

  validateEmail(value) {
    const re = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    return re.test(value);
  }

  updateState() {
    const email = this.emailTarget.value.trim();
    const valid = this.validateEmail(email);

    this.submitTarget.disabled = !valid;
    this.submitTarget.classList.toggle("bg-green-600", valid);
    this.submitTarget.classList.toggle("hover:bg-green-700", valid);
    this.submitTarget.classList.toggle("cursor-pointer", valid);
    this.submitTarget.classList.toggle("bg-red-600", !valid);
    this.submitTarget.classList.toggle("cursor-not-allowed", !valid);
  }

  emailTargetConnected(element) {
    element.addEventListener("input", this.updateState);
  }
}
