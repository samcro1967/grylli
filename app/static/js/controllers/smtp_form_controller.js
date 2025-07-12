// app/static/js/controllers/smtp_form_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["submit"];
  static values = { new: Boolean };

  connect() {
    this.fields = [
      "label",
      "smtp_host",
      "smtp_port",
      "smtp_username",
      "smtp_password"
    ].map(id => document.getElementById(id));

    this.fields.forEach(field => {
      if (field) {
        field.addEventListener("input", () => this.updateButtonState());
      }
    });

    this.updateButtonState();
  }

  updateButtonState() {
    const [label, host, port, username, password] = this.fields;
    this._clearErrors();
    let valid = true;

    if (!this._nonEmpty(label?.value)) {
      this._setError("label", "Label is required.");
      valid = false;
    }
    if (!this._validHost(host?.value)) {
      this._setError("smtp_host", "Enter a valid host.");
      valid = false;
    }
    if (!this._validPort(port?.value)) {
      this._setError("smtp_port", "Enter a valid port (1–65535).");
      valid = false;
    }
    if (!this._nonEmpty(username?.value)) {
      this._setError("smtp_username", "Username is required.");
      valid = false;
    }

    // Require password if this is a new form
    if (!this._nonEmpty(password?.value)) {
      this._setError("smtp_password", "Password is required.");
      valid = false;
    }

    if (this.hasSubmitTarget) {
      this.submitTarget.disabled = !valid;
    }
  }

  _setError(field, message) {
    const el = document.getElementById(`${field}-client-error`);
    if (el) el.textContent = message;
  }

  _clearErrors() {
    this.fields.forEach(f => {
      const el = document.getElementById(`${f.id}-client-error`);
      if (el) el.textContent = "";
    });
  }

  _nonEmpty(str) {
    return str && str.trim().length > 0;
  }

  _validHost(host) {
    return /^[a-zA-Z0-9.-]+$/.test(host) && host.length > 2;
  }

  _validPort(port) {
    const n = parseInt(port, 10);
    return /^\d+$/.test(port) && n >= 1 && n <= 65535;
  }
}
