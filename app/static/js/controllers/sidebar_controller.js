// app/static/js/controllers/sidebar_controller.js

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["desktop", "label", "middle"];

  connect() {
    const stored = localStorage.getItem("sidebarCollapsed");
    this.collapsed = stored === "true";
    this._applyCollapseState();

    // Restore scroll position if available
    this._restoreScrollPosition();

    // Save scroll position on full page unload
    window.addEventListener("beforeunload", this._saveScrollPosition);

    // Prevent layout jump on link clicks
    if (this.hasMiddleTarget) {
      this.middleTarget.addEventListener("click", (event) => {
        const anchor = event.target.closest("a");
        if (anchor) {
          const scrollTop = this.middleTarget.scrollTop;
          requestAnimationFrame(() => {
            this.middleTarget.scrollTop = scrollTop;
          });

          // Toggle Tailwind scroll-behavior classes
          this.middleTarget.classList.add("scroll-auto");
          this.middleTarget.classList.remove("scroll-smooth");

          setTimeout(() => {
            this.middleTarget.classList.remove("scroll-auto");
            this.middleTarget.classList.add("scroll-smooth");
          }, 300);
        }
      });
    }
  }

  disconnect() {
    this._saveScrollPosition(); // Just in case
    window.removeEventListener("beforeunload", this._saveScrollPosition);
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

  _saveScrollPosition = () => {
    if (this.hasMiddleTarget) {
      localStorage.setItem("__GrylliSidebarScrollTop", this.middleTarget.scrollTop);
    }
  };

  _restoreScrollPosition() {
    if (this.hasMiddleTarget) {
      const stored = localStorage.getItem("__GrylliSidebarScrollTop");
      if (stored) {
        this.middleTarget.scrollTop = parseInt(stored, 10);
      }
    }
  }
}
