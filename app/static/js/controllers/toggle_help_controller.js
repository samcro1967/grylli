// static/js/controllers/toggle_help_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["label", "panel"];
  static values = {
    showLabel: String,
    hideLabel: String
  };

  connect() {
    this._updateLabel();
  }

  toggle() {
    this.panelTarget.classList.toggle("hidden");
    this._updateLabel();
  }

  _updateLabel() {
    const isHidden = this.panelTarget.classList.contains("hidden");

    const show = this.hasShowLabelValue ? this.showLabelValue : "Show Help";
    const hide = this.hasHideLabelValue ? this.hideLabelValue : "Hide Help";

    this.labelTarget.textContent = isHidden ? show : hide;
  }

}
