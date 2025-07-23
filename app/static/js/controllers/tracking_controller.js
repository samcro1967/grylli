// ---------------------------------------------------------------------
// tracking_controller.js
// app/static/js/controllers/tracking_controller.js
// Controls letter spacing (tracking): tight / normal / wide
// ---------------------------------------------------------------------

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["selector"];
  static values = {
    key: { type: String, default: "trackingLevel" },
  };

  connect() {
    const saved = localStorage.getItem(this.keyValue);
    if (saved) {
      this.applyTracking(saved);
      this.selectorTarget.value = saved;
    }
  }

  update(event) {
    const value = event.target.value;
    localStorage.setItem(this.keyValue, value);
    this.applyTracking(value);
  }

  applyTracking(level) {
    const html = document.documentElement;
    html.classList.remove("tracking-tight", "tracking-normal", "tracking-wide");
    html.classList.add(level);
  }
}
