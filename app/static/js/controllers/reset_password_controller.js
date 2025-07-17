// reset_password_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = [
    "username",
    "email",
    "password",
    "confirmPassword",
    "submitButton",
    "emailWarning",
    "complexityWarning",
    "mismatchWarning"
  ];

  connect() {
    this._addInputListeners();
    this.validate();
  }

  _addInputListeners() {
    [
      this.usernameTarget,
      this.emailTarget,
      this.passwordTarget,
      this.confirmPasswordTarget
    ].forEach(el => el.addEventListener("input", () => this.validate()));
  }

  validate() {
    const isEmailValid = this._isValidEmail(this.emailTarget.value);
    const isPwComplex = this._meetsComplexity(this.passwordTarget.value);
    const pwMatches = this.passwordTarget.value === this.confirmPasswordTarget.value;
    const allFilled = this.usernameTarget.value.trim() !== "" &&
                      this.passwordTarget.value.trim() !== "" &&
                      this.confirmPasswordTarget.value.trim() !== "";

    // Show/hide warnings
    this.emailWarningTarget.classList.toggle("hidden", isEmailValid);
    this.complexityWarningTarget.classList.toggle("hidden", isPwComplex);
    this.mismatchWarningTarget.classList.toggle("hidden", pwMatches);

    // Enable/disable button
    const valid = allFilled && isEmailValid && isPwComplex && pwMatches;
    this.submitButtonTarget.disabled = !valid;
    this.submitButtonTarget.classList.toggle("bg-green-600", valid);
    this.submitButtonTarget.classList.toggle("bg-red-500", !valid);
  }

  _isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
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
}
