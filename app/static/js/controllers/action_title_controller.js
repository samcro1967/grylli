// action_title_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

/**
 * Sets document title after HTMX loads an action view
 * 
 * Usage:
 * <a
 *   data-controller="action-title"
 *   data-action-title-title-value="Grylli | Messages | Edit"
 *   hx-on:htmx:afterOnLoad="actionTitle.setTitle(event)"
 * >
 */
export default class extends Controller {
  static values = { title: String }

  setTitle() {
    if (this.hasTitleValue) {
      document.title = this.titleValue
    }
  }
}
