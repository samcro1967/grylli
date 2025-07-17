// redirect_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  connect() {
    const targetUrl = "{{ request.referrer or url_for('auth.login') }}";
    if (targetUrl) {
      window.location.href = targetUrl;
    }
  }
}
