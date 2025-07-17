// app/static/js/controllers/list_toggle_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
    static targets = ["tableView", "cardView", "tableBtn", "cardBtn", "instructions", "toggleText"];
    static values = {
        storageKey: { type: String, default: "listView" },
        showLabel: String,
        hideLabel: String
    };

    connect() {
        const saved = localStorage.getItem(this.storageKeyValue);
        if (saved === "card") {
            this.showCard();
        } else {
            this.showTable();
        }

        if (this.hasInstructionsTarget && this.hasToggleTextTarget) {
            this._updateInstructionLabel(!this.instructionsTarget.classList.contains("hidden"));
        }
    }

    showTable() {
        this._toggleViews("table");
    }

    showCard() {
        this._toggleViews("card");
    }

    toggleInstructions() {
        const visible = this.instructionsTarget.classList.toggle("hidden") === false;
        this._updateInstructionLabel(visible);
    }

    _toggleViews(view) {
        const isCard = view === "card";

        this.cardViewTarget.classList.toggle("hidden", !isCard);
        this.tableViewTarget.classList.toggle("hidden", isCard);

        this.cardBtnTarget.classList.toggle("bg-blue-600", isCard);
        this.cardBtnTarget.classList.toggle("text-white", isCard);
        this.cardBtnTarget.classList.toggle("bg-gray-300", !isCard);
        this.cardBtnTarget.classList.toggle("text-black", !isCard);

        this.tableBtnTarget.classList.toggle("bg-blue-600", !isCard);
        this.tableBtnTarget.classList.toggle("text-white", !isCard);
        this.tableBtnTarget.classList.toggle("bg-gray-300", isCard);
        this.tableBtnTarget.classList.toggle("text-black", isCard);

        localStorage.setItem(this.storageKeyValue, view);
    }

    _updateInstructionLabel(visible) {
        if (!this.hasToggleTextTarget) return;
        this.toggleTextTarget.textContent = visible
            ? this.hideLabelValue
            : this.showLabelValue;
    }
}
