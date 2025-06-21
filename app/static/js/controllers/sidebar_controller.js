// app/static/js/controllers/sidebar_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["desktop", "label", "middle"];

  connect() {
    const stored = localStorage.getItem("sidebarCollapsed");
    this.collapsed = stored === "true";
    this._applyCollapseState();

    // ✅ Prevent layout jump: intercept link clicks and blur immediately
    if (this.hasMiddleTarget) {
      this.middleTarget.addEventListener("click", (event) => {
        const anchor = event.target.closest("a");
        if (anchor) {
          // ✅ Lock scroll position during flicker
          const scrollTop = this.middleTarget.scrollTop;

          requestAnimationFrame(() => {
            this.middleTarget.scrollTop = scrollTop;
          });

          // Optional: hard-block transition effects here if needed
          this.middleTarget.style.scrollBehavior = "auto";
          setTimeout(() => {
            this.middleTarget.style.scrollBehavior = "";
          }, 300);
        }
      });
    }
  }

  toggleCollapsed() {
    this.collapsed = !this.collapsed;
    localStorage.setItem("sidebarCollapsed", this.collapsed);
    this._applyCollapseState();
  }

  _applyCollapseState() {
    if (!this.hasDesktopTarget) return;

    this.desktopTarget.classList.toggle("w-64", !this.collapsed);
    this.desktopTarget.classList.toggle("w-20", this.collapsed);

    this.labelTargets.forEach((el) => {
      el.classList.toggle("hidden", this.collapsed);
    });
  }
}
