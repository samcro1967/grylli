// ---------------------------------------------------------------------
// contrast_controller.js
// app/static/js/controllers/contrast_controller.js
// Sets global contrast level via class on <html>
// ---------------------------------------------------------------------
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["select"];

  connect() {
    const saved = localStorage.getItem("grylli-contrast") || "default";
    this.applyContrast(saved);

    if (this.hasSelectTarget) {
      this.selectTarget.value = saved;
    }
  }

  change(event) {
    const value = event.target.value;
    localStorage.setItem("grylli-contrast", value);
    this.applyContrast(value);
  }

  applyContrast(value) {
    const html = document.documentElement;
    html.classList.remove("contrast-low", "contrast-high");

    if (value === "low") {
      html.classList.add("contrast-low");
    } else if (value === "high") {
      html.classList.add("contrast-high");
    }
    // default = no class applied
  }
}
