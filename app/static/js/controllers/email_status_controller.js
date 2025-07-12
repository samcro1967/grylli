// static/js/controllers/email_status_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  connect() {
    this.fetchStatuses();
    this.interval = setInterval(() => this.fetchStatuses(), 15000);
  }

  disconnect() {
    clearInterval(this.interval);
  }

  fetchStatuses() {
    fetch('/grylli/email/status')
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
          button.innerHTML = isOn
            ? `<span class="text-green-600" title="Email is enabled">🟢</span>`
            : `<span class="text-red-500" title="Email is disabled">🔴</span>`;
        });
      })
      .catch(err => console.error("Failed to fetch email statuses:", err));
  }
}
