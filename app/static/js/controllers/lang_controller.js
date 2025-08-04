// lang_controller.js

import { Controller } from "../vendor/stimulus.js";

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
