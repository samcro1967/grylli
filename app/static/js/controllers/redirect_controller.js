// redirect_controller.js
import { Controller } from "../vendor/stimulus.js";

export default class extends Controller {
  connect() {
    const targetUrl = "{{ request.referrer or url_for('auth.login') }}";
    if (targetUrl) {
      window.location.href = targetUrl;
    }
  }
}
