// list_toggle_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
    static targets = ["tableView", "cardView", "tableBtn", "cardBtn", "instructions", "toggleText"];
    static values = {
        storageKey: String,
        showLabel: String,
        hideLabel: String
    };

    connect() {
        const view = localStorage.getItem(this.storageKeyValue) || "table";
        this.toggleView(view);
    }

    showTable() {
        this.toggleView("table");
    }

    showCard() {
        this.toggleView("card");
    }

    toggleInstructions() {
        this.instructionsTarget.classList.toggle("hidden");
        this.toggleTextTarget.textContent =
            this.instructionsTarget.classList.contains("hidden") ?
            this.showLabelValue : this.hideLabelValue;
    }

    toggleView(view) {
        const isTable = view === "table";
        this.tableViewTarget.classList.toggle("hidden", !isTable);
        this.cardViewTarget.classList.toggle("hidden", isTable);

        this.tableBtnTarget.classList.toggle("bg-blue-600", isTable);
        this.tableBtnTarget.classList.toggle("text-white", isTable);
        this.tableBtnTarget.classList.toggle("bg-gray-300", !isTable);
        this.tableBtnTarget.classList.toggle("text-black", !isTable);

        this.cardBtnTarget.classList.toggle("bg-blue-600", !isTable);
        this.cardBtnTarget.classList.toggle("text-white", !isTable);
        this.cardBtnTarget.classList.toggle("bg-gray-300", isTable);
        this.cardBtnTarget.classList.toggle("text-black", isTable);

        localStorage.setItem(this.storageKeyValue, view);
    }
}
