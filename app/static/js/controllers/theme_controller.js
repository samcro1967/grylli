// app/static/js/controllers/theme_controller.js

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["knob"];

  connect() {
    // No need to re-apply theme — server already applied correct class based on cookie
    const isDark = document.documentElement.classList.contains("dark");
    this.updateKnob(isDark);
  }

  toggle() {
    const isDark = document.documentElement.classList.toggle("dark");

    // Set a cookie that persists for 1 year
    document.cookie = `theme=${isDark ? "dark" : "light"}; path=/; max-age=31536000; samesite=lax`;

    this.updateKnob(isDark);
  }

  updateKnob(isDark) {
    if (!this.hasKnobTarget) return;
    this.knobTarget.classList.toggle("rotate-180", isDark);
  }
}
