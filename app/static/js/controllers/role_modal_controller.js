import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
    static targets = [
        "instructions",
        "toggleText",
        "modal",
        "username",
        "form",
        "userIdInput",
        "roleInputs",
        "saveButton"
    ];

	connect() {
		this.showingInstructions = false;
		this.selectedUserId = null;
		this.selectedUsername = null;
		this.selectedRole = null;

		this.roleChangeBase = document.body.dataset.roleChangeBase;
	}


    toggleInstructions() {
        this.showingInstructions = !this.showingInstructions;
        this.instructionsTarget.classList.toggle("hidden", !this.showingInstructions);
        this.toggleTextTarget.textContent = this.showingInstructions
            ? this.data.get("hideText")
            : this.data.get("showText");
    }

	openModal(event) {
		const userId = event.target.dataset.roleModalParamsId;
		const username = event.target.dataset.roleModalParamsUsername;
		const role = event.target.dataset.roleModalParamsRole;

		this.selectedUserId = userId;
		this.selectedUsername = username;
		this.selectedRole = role;

		// Update the modal with the selected user's info
		this.userIdInputTarget.value = this.selectedUserId;
		this.usernameTarget.textContent = this.selectedUsername;

		// Set the role radio input based on the selected role
		this.roleInputsTargets.forEach(input => {
			input.checked = input.value === this.selectedRole;
		});

		// Set the form action dynamically
		this.formTarget.action = this.roleChangeBase.replace("0", this.selectedUserId);

		// Show the modal
		this.modalTarget.classList.remove("hidden");
	}

    closeModal() {
        // Hide the modal
        this.modalTarget.classList.add("hidden");
    }

    enableSave() {
        // Enable the save button
        this.saveButtonTarget.disabled = false;
    }
}
