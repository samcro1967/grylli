// app/static/js/controllers/forgot_password_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["username", "email"];

  connect() {
    this._validate();
    this.usernameTarget.addEventListener("input", () => this._validate());
    this.emailTarget.addEventListener("input", () => this._validate());
  }

  _isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  _validate() {
    const emailValid = this._isValidEmail(this.emailTarget.value.trim());
    this.emailTarget.setAttribute("aria-invalid", String(!emailValid));

    const usernameFilled = this.usernameTarget.value.trim() !== "";
    this.usernameTarget.setAttribute("aria-invalid", String(!usernameFilled));
  }
}
