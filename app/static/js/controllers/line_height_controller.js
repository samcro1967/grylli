// ---------------------------------------------------------------------
// line_height_controller.js
// Controls line height (reading density): tight / normal / loose
// ---------------------------------------------------------------------

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["selector"];
  static values = {
    key: { type: String, default: "lineHeightLevel" },
  };

  connect() {
    const saved = localStorage.getItem(this.keyValue);
    if (saved) {
      this.applyLineHeight(saved);
      this.selectorTarget.value = saved;
    }
  }

  update(event) {
    const value = event.target.value;
    localStorage.setItem(this.keyValue, value);
    this.applyLineHeight(value);
  }

  applyLineHeight(level) {
    const html = document.documentElement;
    html.classList.remove("leading-tight", "leading-normal", "leading-loose");
    html.classList.add(level);
  }
}
