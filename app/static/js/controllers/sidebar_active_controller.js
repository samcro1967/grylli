/**
 * app/static/js/controllers/sidebar_active_controller.js
 * Highlights the active sidebar link and updates document.title via HTMX.
 * Works with hx-push-url, native clicks, and tabs.
 */


import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["link"];

  connect() {
    this.highlightActiveLink();
    this.updateTitleFromActiveLink();

    document.addEventListener("htmx:afterSettle", () => {
      this.highlightActiveLink();
      this.updateTitleFromActiveLink();
    });
  }

  highlightActiveLink() {
    const currentPath = window.location.pathname;

    this.linkTargets.forEach((el) => {
      const prefix = el.getAttribute("data-path-prefix");
      if (prefix && currentPath.startsWith(prefix)) {
        el.classList.add("bg-base-200", "font-bold");
      } else {
        el.classList.remove("bg-base-200", "font-bold");
      }
    });
  }

  updateTitleFromActiveLink() {
    const currentPath = window.location.pathname;
    // console.log("📍 Checking title at:", currentPath);

    this.linkTargets.forEach((el, i) => {
      const prefix = el.getAttribute("data-path-prefix");
      const title = el.getAttribute("data-sidebar-title");

      // console.log(`🔗 [${i}] Element:`, el.outerHTML);
      // console.log(`   ↪️ prefix:`, prefix);
      // console.log(`   ↪️ title:`, title);

      if (prefix && currentPath.startsWith(prefix) && title) {
        // console.log("✅ MATCHED — setting title to:", title);
        document.title = title;
      }
    });
  }

}
