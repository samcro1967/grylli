// app/static/js/controllers/insecure_warning_controller.js
import { Controller } from "../vendor/stimulus.js";

export default class extends Controller {
  connect() {
    if (location.protocol === "http:" && location.hostname !== "localhost") {
      this.element.classList.remove("hidden");
    }
  }
}
