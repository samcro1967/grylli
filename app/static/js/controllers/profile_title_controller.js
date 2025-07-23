// ---------------------------------------------------------------------
// profile_title_controller.js
// app/static/js/controllers/profile_title_controller.js
// Sets document.title for profile dropdown HTMX links
// ---------------------------------------------------------------------

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js"

export default class extends Controller {
  connect() {
    this.element.addEventListener("htmx:afterOnLoad", (event) => {
      const trigger = event.detail.elt
      const title = trigger?.getAttribute("data-profile-title")
      if (title) {
        document.title = title
      }
    })
  }
}
