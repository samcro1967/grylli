// static/js/controllers/user_form_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = [
    "username",
    "email",
    "currentPassword",
    "password",
    "confirmPassword",
    "submitButton",
    "emailWarning",
    "complexityWarning",
    "mismatchWarning",
    "currentPasswordWarning"
  ];

  connect() {
    this.validateForm();
    this.element.addEventListener("input", () => this.validateForm());
  }

  validateForm() {
    const username = this.usernameTarget?.value.trim() || "";
    const email = this.emailTarget?.value.trim() || "";
    const password = this.passwordTarget?.value || "";
    const confirmPassword = this.confirmPasswordTarget?.value || "";
    const currentPassword = this.hasCurrentPasswordTarget ? this.currentPasswordTarget.value : "";

    const emailValid = email.includes("@") && email.includes(".");
    const passwordValid =
      password.length >= 8 &&
      /[a-z]/.test(password) &&
      /[A-Z]/.test(password) &&
      /\d/.test(password) &&
      /[^a-zA-Z0-9]/.test(password);
    const passwordsMatch = password === confirmPassword;

    // Only require currentPassword if the field exists
    const allPresent = this.hasCurrentPasswordTarget
      ? username && email && password && confirmPassword && currentPassword
      : username && email && password && confirmPassword;

    const valid = allPresent && emailValid && passwordValid && passwordsMatch;

    // Enable or disable the submit button
    this.submitButtonTarget.disabled = !valid;

    // Reset and apply color classes
    this.submitButtonTarget.classList.remove(
      "bg-red-500",
      "hover:bg-red-600",
      "bg-green-600",
      "hover:bg-green-700"
    );

    if (valid) {
      this.submitButtonTarget.classList.add("bg-green-600", "hover:bg-green-700");
    } else {
      this.submitButtonTarget.classList.add("bg-red-500", "hover:bg-red-600");
    }

    // Toggle validation warnings
    if (this.hasEmailWarningTarget) {
      this.emailWarningTarget.classList.toggle("hidden", emailValid);
    }

    if (this.hasComplexityWarningTarget) {
      this.complexityWarningTarget.classList.toggle("hidden", passwordValid);
    }

    if (this.hasMismatchWarningTarget) {
      this.mismatchWarningTarget.classList.toggle("hidden", passwordsMatch);
    }

    if (this.hasCurrentPasswordWarningTarget) {
      this.currentPasswordWarningTarget.classList.toggle("hidden", !!currentPassword);
    }
  }
}
