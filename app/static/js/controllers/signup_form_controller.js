// signup_form_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = [
    "username",
    "email",
    "password",
    "confirmPassword",
    "pin",
    "mismatchWarning",
    "complexityWarning",
    "emailWarning"
  ];

  connect() {
    this.validate();
    this._attachInputListeners();
  }

  validate() {
    const isEmailValid = this._isValidEmail(this.emailTarget.value);
    const isPwComplex = this._meetsComplexity(this.passwordTarget.value);
    const pwMatches = this.passwordTarget.value === this.confirmPasswordTarget.value;

    this.emailWarningTarget.classList.toggle("hidden", isEmailValid);
    this.complexityWarningTarget.classList.toggle("hidden", isPwComplex);
    this.mismatchWarningTarget.classList.toggle("hidden", pwMatches);
  }

  _attachInputListeners() {
    [
      this.usernameTarget,
      this.emailTarget,
      this.passwordTarget,
      this.confirmPasswordTarget,
      this.pinTarget
    ].forEach(field => {
      field.addEventListener("input", () => this.validate());
    });
  }

  _meetsComplexity(password) {
    return (
      password.length >= 8 &&
      /[A-Z]/.test(password) &&
      /[a-z]/.test(password) &&
      /[0-9]/.test(password) &&
      /[!@#$%^&*(),.?":{}|<>]/.test(password)
    );
  }

  _isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }
}
