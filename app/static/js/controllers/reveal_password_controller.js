// static/js/controllers/reveal_password_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  show(event) {
    const input = this._findInput(event);
    if (input) {
      input.type = "text";
    }
  }

  hide(event) {
    const input = this._findInput(event);
    if (input) {
      input.type = "password";
    }
  }

  _findInput(event) {
    const button = event.currentTarget;
    const wrapper = button?.closest("[data-controller~='reveal-password']");
    return wrapper?.querySelector("input[type]");
  }
}
