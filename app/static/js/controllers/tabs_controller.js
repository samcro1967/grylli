// static/js/controllers/tabs_controller.js
import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["tab"];
  static values = {
    activeTab: String,
  };

  connect() {
    let defaultTab = this.tabTargets[0];

    let tabName = this.activeTabValue;

    // 🔁 If activeTab not set from data, parse from URL (e.g., /overview/schedule/)
    if (!tabName) {
      const match = window.location.pathname.match(/\/overview\/(\w+)\//);
      if (match && match[1]) {
        tabName = match[1];
      }
    }

    if (tabName) {
      const selector = `[data-tabs-name="${tabName}"]`;
      const match = this.tabTargets.find((el) => el.matches(selector));
      if (match) {
        defaultTab = match;
      }
    }

    this.activate(defaultTab);
  }

  activate(eventOrElement) {
    const clicked = eventOrElement.target || eventOrElement;

    this.tabTargets.forEach((tab) => {
      tab.classList.remove("font-bold", "text-primary");
    });

    clicked.classList.add("font-bold", "text-primary");

    // ✅ Update document title if provided
    const newTitle = clicked.getAttribute("data-tabs-title");
    if (newTitle) {
      document.title = newTitle;
    }
  }

}
