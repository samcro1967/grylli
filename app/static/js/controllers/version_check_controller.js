// app/static/js/controllers/version_check_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static values = { statusUrl: String };

  connect() {
    if (!this.statusUrlValue) {
      console.warn("[version-check] ⚠️ statusUrlValue is missing.");
      return;
    }

    const url = new URL(this.statusUrlValue, window.location.origin);

    fetch(url)
      .then(response => response.json())
      .then(data => this._render(data))
      .catch(() => this._render({ error: true }));
  }

  _render({ current_version, latest_version, github_url, error }) {
    this.element.innerHTML = "";  // Safe, static root clearing

    const wrapper = document.createElement("div");
    wrapper.className = "flex items-center space-x-2 text-sm px-2 py-1";

    const icon = document.createElement("i");
    icon.classList.add("fas", "text-lg");

    const label = document.createElement("span");
    label.setAttribute("data-sidebar-target", "label");

    if (error) {
      icon.classList.add("fa-times-circle", "text-error");
      label.textContent = "Version check failed";
      wrapper.title = "Version check failed";
    } else if (current_version === latest_version) {
      icon.classList.add("fa-check-circle", "text-success");
      label.textContent = `Grylli is up to date (v${current_version})`;
      wrapper.title = label.textContent;
    } else {
      icon.classList.add("fa-rocket", "text-warning");

      const link = document.createElement("a");
      link.href = `${github_url}/releases`;
      link.className = "underline hover:text-warning-focus";
      link.textContent = `New version available: ${latest_version}`;

      label.appendChild(link);
      wrapper.title = `New version available: ${latest_version}`;
    }

    wrapper.appendChild(icon);
    wrapper.appendChild(label);
    this.element.appendChild(wrapper);
    this.element.classList.remove("hidden");
  }
}
