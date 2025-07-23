// ---------------------------------------------------------------------
// font_size_controller.js
// app/static/js/controllers/font_size_controller.js
// Stimulus controller to manage root font size for scaling text globally
// ---------------------------------------------------------------------
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["select"];

  connect() {
    const saved = localStorage.getItem("grylli-font-size") || "100";

    setTimeout(() => {
      this.applyFontSize(saved);
      if (this.hasSelectTarget) {
        this.selectTarget.value = saved;
      }
    }, 10);
  }

  update(event) {
    const value = event.target.value;
    localStorage.setItem("grylli-font-size", value);
    this.applyFontSize(value);
  }

  applyFontSize(percent) {
    document.documentElement.style.fontSize = `${percent}%`;
  }
}
