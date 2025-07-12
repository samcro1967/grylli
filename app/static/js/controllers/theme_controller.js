// app/static/js/controllers/theme_controller.js

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["knob", "select"];

  async connect() {
    try {
      const response = await fetch("/grylli/static/daisyui-themes.json");
      this.themes = await response.json();

      if (this.hasSelectTarget) {
        this.selectTarget.innerHTML = this.themes
          .map(t => `<option value="${t}">${t.charAt(0).toUpperCase() + t.slice(1)}</option>`)
          .join("");
      }

      const theme = this.getCookie("theme") || this.themes[0] || "light";
      document.documentElement.setAttribute("data-theme", theme);

      if (this.hasSelectTarget) {
        this.selectTarget.value = theme;
      }

      this.updateKnob(theme);
    } catch (error) {
      console.error("Failed to load themes:", error);
    }
  }

  async change() {
    const newTheme = this.selectTarget.value;
    document.documentElement.setAttribute("data-theme", newTheme);
    document.cookie = `theme=${newTheme}; path=/; max-age=31536000; samesite=lax`;
    this.updateKnob(newTheme);

    // 🔹 Send theme change log to server
    try {
      await fetch("/grylli/meta/log-theme-change", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ theme: newTheme }),
      });
    } catch (error) {
      console.warn("Failed to log theme change:", error);
    }
  }

  updateKnob(theme) {
    if (!this.hasKnobTarget) return;
    this.knobTarget.classList.toggle("rotate-180", theme === "dark");
  }

  getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
  }
}
