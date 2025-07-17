// static/js/controllers/confirm_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static values = { message: String }

  connect() {
    requestAnimationFrame(() => {
      this.element.addEventListener("submit", this.confirm.bind(this));
    });
  }

  confirm(event) {
    console.log("[confirm_controller] Showing message:", this.messageValue);
    if (!window.confirm(this.messageValue)) {
      event.preventDefault();
    }
  }

}
