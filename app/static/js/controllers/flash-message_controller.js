// app/static/js/controllers/flash-message_controller.js

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static values = { messages: Array };

  connect() {
    const messages = this.messagesValue;
    if (!messages || messages.length === 0) return;

    // Remove old messages
    document.querySelectorAll(".flash-toast").forEach(el => el.remove());

    const message = messages[0];
    const div = document.createElement("div");
    div.className =
      "flash-toast fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 " +
      "bg-green-600 text-white font-medium text-sm px-6 py-2 rounded-lg shadow-lg max-w-fit text-center " +
      "opacity-0 transition-opacity duration-500";

    div.textContent = message;

    document.body.appendChild(div);

    // Trigger fade-in using class toggling
    requestAnimationFrame(() => {
      div.classList.remove("opacity-0");
      div.classList.add("opacity-100");
    });

    setTimeout(() => {
      div.classList.remove("opacity-100");
      div.classList.add("opacity-0");
      div.addEventListener("transitionend", () => div.remove());
    }, 5000);
  }
}
