// ---------------------------------------------------------------------
// sidebar_controller.js
// app/static/js/controllers/sidebar_controller.js
// Stimulus controller for sidebar collapse state.
// ---------------------------------------------------------------------

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["desktop", "label", "icon"];

  connect() {
    this.collapsed = localStorage.getItem("sidebarCollapsed") === "true";
    this._applyCollapseState();
  }

  toggleCollapsed() {
    this.collapsed = !this.collapsed;
    localStorage.setItem("sidebarCollapsed", this.collapsed);
    this._applyCollapseState();
  }

  _applyCollapseState() {
    if (this.hasDesktopTarget) {
      this.desktopTarget.classList.toggle("w-16", this.collapsed);
      this.desktopTarget.classList.toggle("w-64", !this.collapsed);
    }

    if (this.hasLabelTarget) {
      this.labelTargets.forEach((el) => {
        el.classList.toggle("hidden", this.collapsed);
      });
    }

    if (this.hasIconTarget) {
      this.iconTargets.forEach((el) => {
        el.classList.toggle("rotate-180", this.collapsed);
      });
    }
  }
}
