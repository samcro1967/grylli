import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["knob"];

  connect() {
    requestAnimationFrame(() => this.applyStoredTheme());
  }

  toggle() {
    const isDark = document.documentElement.classList.toggle("dark");
    localStorage.setItem("theme", isDark ? "dark" : "light");
    this.updateKnob(isDark);
  }

	applyStoredTheme() {
	  const stored = localStorage.getItem("theme");
	  const isDark = stored === "dark";
	  const alreadyDark = document.documentElement.classList.contains("dark");

	  if (isDark && !alreadyDark) {
		document.documentElement.classList.add("dark");
	  } else if (!isDark && alreadyDark) {
		document.documentElement.classList.remove("dark");
	  }

	  this.updateKnob(isDark);
	}

  updateKnob(isDark) {
    if (!this.hasKnobTarget) return;
    // Add custom knob logic here, e.g., animation or icon flip
    this.knobTarget.classList.toggle("rotate-180", isDark);
  }
}
