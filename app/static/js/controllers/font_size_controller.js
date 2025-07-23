// ---------------------------------------------------------------------
// font_size_controller.js
// app/static/js/controllers/font_size_controller.js
// Stimulus controller to manage root font size for scaling text globally
// ---------------------------------------------------------------------
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static values = {
    default: Number
  }

  connect() {
    const saved = localStorage.getItem("fontSizePercent");
    const size = saved || this.defaultValue || 100;
    this.setFontSize(size);
  }

  update(event) {
    const size = event.target.value;
    localStorage.setItem("fontSizePercent", size);
    this.setFontSize(size);
  }

  setFontSize(percent) {
    document.documentElement.style.fontSize = `${percent}%`;
  }
}
