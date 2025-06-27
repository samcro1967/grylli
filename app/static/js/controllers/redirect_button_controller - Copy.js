// static/js/controllers/redirect_button_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static values = { url: String }

  go() {
    window.location.href = this.urlValue
  }
}
