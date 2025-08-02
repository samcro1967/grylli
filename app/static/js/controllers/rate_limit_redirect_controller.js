// rate_limit_redirect_controller.js
import { Controller } from "../vendor/stimulus.js";

export default class extends Controller {
  static values = {
    delay: Number,
    url: String
  }

  connect() {
    this.remaining = this.delayValue;
    this.delaySpan = this.element.querySelector("#delay");
    this.startCountdown();
  }

  startCountdown() {
    this.updateDisplay();

    if (this.remaining <= 0) {
      window.location.href = this.urlValue;
      return;
    }

    this.timer = setInterval(() => {
      this.remaining -= 1;
      this.updateDisplay();

      if (this.remaining <= 0) {
        clearInterval(this.timer);
        window.location.href = this.urlValue;
      }
    }, 1000);
  }

  updateDisplay() {
    if (this.delaySpan) {
      this.delaySpan.textContent = this.remaining;
    }
  }

  disconnect() {
    if (this.timer) {
      clearInterval(this.timer);
    }
  }
}
