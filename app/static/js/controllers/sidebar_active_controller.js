/**
 * app/static/js/controllers/sidebar_active_controller.js
 * Highlights the currently active sidebar link based on location.pathname.
 * Works with HTMX navigation (hx-push-url) and is CSP-compliant.
 */

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["link"]

  connect() {
    this.highlightActiveLink()
    document.addEventListener("htmx:afterSettle", () => this.highlightActiveLink())
  }

  highlightActiveLink() {
    const currentPath = window.location.pathname

    this.linkTargets.forEach((el) => {
      const matchPrefix = el.getAttribute("data-path-prefix")
      if (matchPrefix && currentPath.startsWith(matchPrefix)) {
        el.classList.add("bg-base-200", "font-bold")
      } else {
        el.classList.remove("bg-base-200", "font-bold")
      }
    })
  }
}
