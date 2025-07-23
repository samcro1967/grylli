// ---------------------------------------------------------------------
// roundedness_controller.js
// app/static/js/controllers/roundedness_controller.js
// Toggles rounded-none class on <html> and persists via localStorage
// ---------------------------------------------------------------------
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["select"];

  connect() {
    const saved = localStorage.getItem("grylli-rounded") || "default";

    setTimeout(() => {
      this.applyRoundedness(saved);
      if (this.hasSelectTarget) {
        this.selectTarget.value = saved;
      }
    }, 10);
  }

  update(event) {
    const value = event.target.value;
    localStorage.setItem("grylli-rounded", value);
    this.applyRoundedness(value);
  }

  applyRoundedness(value) {
    const html = document.documentElement;
    html.classList.remove("rounded-none", "rounded-lg", "rounded-xl");

    if (value === "none") {
      html.classList.add("rounded-none");
    } else if (value === "xl") {
      html.classList.add("rounded-xl");
    }
  }
}
