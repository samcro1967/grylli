// app/static/js/controllers/background_controller.js

import { Controller } from "../vendor/stimulus.js";

export default class extends Controller {
  static targets = ["select"];

  async connect() {
    try {
      const base = window.BASE_URL || "";
      const response = await fetch(`${base}/meta/static/background-patterns.json`);
      this.patterns = await response.json();

      if (this.hasSelectTarget) {
        this.selectTarget.replaceChildren();  // Clear existing options

        this.patterns.forEach(p => {
          const option = document.createElement("option");
          option.value = p.file;
          option.textContent = this.label(p.name);
          this.selectTarget.appendChild(option);
        });
      }

      const saved = localStorage.getItem("background") || "none";
      this.apply(saved);
      if (this.hasSelectTarget) this.selectTarget.value = saved;
    } catch (err) {
      console.error("Failed to load background patterns:", err);
    }
  }

  change(event) {
    const selected = event.target.value;
    this.apply(selected);
    localStorage.setItem("background", selected);
  }

  apply(file) {
    const target = document.querySelector("#main-content");
    if (!target) return;

    const base = window.BASE_URL || "";
    const url = file === "none" ? "none" : `url('${base}/static/${file}')`;
    target.style.backgroundImage = url;
  }

  label(name) {
    return name.replace(/[-_]/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  }
}
