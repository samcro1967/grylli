// app/static/js/controllers/webhook_list_toggle_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
    static targets = ["tableView", "cardView", "tableBtn", "cardBtn", "instructions"];
    static values = {
        storageKey: { type: String, default: "webhookListView" },
        showLabel: String,
        hideLabel: String
    };

    connect() {
        const saved = localStorage.getItem(this.storageKeyValue);
        this._toggleView(saved || "table");
    }

    showTable() {
        this._toggleView("table");
    }

    showCard() {
        this._toggleView("card");
    }

    _toggleView(view) {
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

        if (this.hasInstructionsTarget) {
            this.instructionsTarget.classList.toggle("hidden", !isTable);
        }

        localStorage.setItem(this.storageKeyValue, view);
    }
}
