// app/static/js/controllers/background_controller.js

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["select"];

  async connect() {
    try {
      const response = await fetch("/grylli/meta/static/background-patterns.json");
      this.patterns = await response.json();

      if (this.hasSelectTarget) {
        this.selectTarget.innerHTML = this.patterns
          .map(p => `<option value="${p.file}">${this.label(p.name)}</option>`)
          .join("");
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

    const url = file === "none" ? "none" : `url('/grylli/static/${file}')`;
    target.style.backgroundImage = url;
  }

  label(name) {
    return name.replace(/[-_]/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  }
}
