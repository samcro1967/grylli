// static/js/controllers/email_status_controller.js
import { Controller } from "../vendor/stimulus.js";

export default class extends Controller {
  connect() {
    this.fetchStatuses();
    this.interval = setInterval(() => this.fetchStatuses(), 15000);
  }

  disconnect() {
    clearInterval(this.interval);
  }

  fetchStatuses() {
    const base = window.BASE_URL || "";

    fetch(`${base}/email/status`)
      .then(response => response.json())
      .then(data => {
        data.forEach(email => {
          const button = document.querySelector(
            `form[action*='${email.id}'] button[title='Toggle Email On/Off']`
          );
          if (!button) return;

          const isOn = email.is_enabled;
          button.classList.toggle('text-red-500', !isOn);
          button.classList.toggle('text-green-600', isOn);
          const span = document.createElement("span");
          span.className = isOn ? "text-green-600" : "text-red-500";
          span.title = isOn ? "Email is enabled" : "Email is disabled";
          span.textContent = isOn ? "🟢" : "🔴";

          button.replaceChildren(span);
        });
      })
      .catch(err => console.error("Failed to fetch email statuses:", err));
  }
}
