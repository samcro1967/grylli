// app/static/js/controllers/sidebar_controller.js

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["desktop", "label", "middle", "icon"];

  connect() {
    const stored = localStorage.getItem("sidebarCollapsed");
    this.collapsed = stored === "true";

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        this._applyCollapseState(); // ✅ wait until fully rendered
      });
    });

    this._restoreScrollPosition();

    window.addEventListener("beforeunload", this._saveScrollPosition);

    if (this.hasMiddleTarget) {
      this.middleTarget.addEventListener("click", (event) => {
        const anchor = event.target.closest("a");
        if (anchor) {
          const scrollTop = this.middleTarget.scrollTop;
          requestAnimationFrame(() => {
            this.middleTarget.scrollTop = scrollTop;
          });

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
    this.desktopTarget.classList.toggle("w-[88px]", this.collapsed);

    this.labelTargets.forEach((el) => el.classList.toggle("hidden", this.collapsed));
    this.iconTargets?.forEach((el) => el.classList.toggle("hidden", !this.collapsed));

    // Optional: adjust icon padding
    this.desktopTarget.querySelectorAll(".icon-wrapper").forEach((el) => {
      el.classList.toggle("pl-6", !this.collapsed);
      el.classList.toggle("pl-2", this.collapsed);
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
