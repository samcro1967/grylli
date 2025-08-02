// static/js/controllers/redirect_button_controller.js
import { Controller } from "../vendor/stimulus.js";

export default class extends Controller {
  static values = { url: String }

  go() {
    window.location.href = this.urlValue
  }
}
