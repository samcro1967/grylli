// app/static/js/controllers/version_check_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static values = { statusUrl: String };

  connect() {
    if (!this.statusUrlValue) {
      console.warn("[version-check] ⚠️ statusUrlValue is missing or undefined.");
      return;
    }

    const fullUrl = new URL(this.statusUrlValue, window.location.origin);

    fetch(fullUrl)
      .then(response => response.json())
      .then(data => {
        const { current_version, latest_version, github_url } = data;

        if (!latest_version) {
          this._renderMessage("❓ Version info unavailable", "text-gray-500");
          return;
        }

        if (current_version === latest_version) {
          this._renderMessage(
            `<span class="text-green-700 dark:text-green-300">✔ Grylli is up to date (v${current_version})</span>`
          );
        } else {
          this._renderMessage(
            `<span class="text-yellow-500 dark:text-yellow-300">🚀 <a href="${github_url}/releases" class="underline hover:text-yellow-600">New version available: v${latest_version}</a></span>`
          );
        }
      })
      .catch(err => {
        this._renderMessage(
          `<span class="text-red-500 dark:text-red-400">❌ Version check failed</span>`
        );
      });
  }

  _renderMessage(innerHtml) {
    this.element.innerHTML = innerHtml;
    this.element.classList.remove("hidden");
    this.element.className = "flex items-center space-x-1 text-sm text-zinc-700 dark:text-zinc-100 px-2 py-1";
  }
}
