import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = [
    "username", "email", "password", "confirmPassword",
    "submitButton", "mismatchWarning", "complexityWarning", "emailWarning"
  ];

  connect() {
    this.validate();
    [this.usernameTarget, this.emailTarget, this.passwordTarget, this.confirmPasswordTarget].forEach(el =>
      el.addEventListener("input", this.validate.bind(this))
    );
  }

  validate() {
    const valid = this.allFieldsValid();
    this.mismatchWarningTarget.classList.toggle("hidden", this.passwordsMatch());
    this.complexityWarningTarget.classList.toggle("hidden", this.meetsComplexity(this.passwordTarget.value));
    this.emailWarningTarget.classList.toggle("hidden", this.isValidEmail(this.emailTarget.value));
    this.submitButtonTarget.disabled = !valid;
    this.submitButtonTarget.classList.toggle("bg-green-600", valid);
    this.submitButtonTarget.classList.toggle("bg-red-500", !valid);
  }

  allFieldsValid() {
    return (
      this.usernameTarget.value.trim() !== "" &&
      this.isValidEmail(this.emailTarget.value) &&
      this.passwordTarget.value.trim() !== "" &&
      this.confirmPasswordTarget.value.trim() !== "" &&
      this.passwordsMatch() &&
      this.meetsComplexity(this.passwordTarget.value)
    );
  }

  passwordsMatch() {
    return this.passwordTarget.value === this.confirmPasswordTarget.value;
  }

  meetsComplexity(password) {
    return (
      password.length >= 8 &&
      /[A-Z]/.test(password) &&
      /[a-z]/.test(password) &&
      /[0-9]/.test(password) &&
      /[!@#$%^&*(),.?":{}|<>]/.test(password)
    );
  }

  isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
}
