import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["select"];

  change() {
    const langCode = this.selectTarget.value;
    const baseUrl = this.selectTarget.dataset.baseUrl;
    if (langCode && baseUrl) {
      window.location.href = baseUrl + langCode;
    }
  }
}
