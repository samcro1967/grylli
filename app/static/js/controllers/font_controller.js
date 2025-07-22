// static/js/controllers/font_controller.js

import { Controller } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

import { FONT_CLASSES, FONT_FAMILIES } from "../font_config.js";

export default class FontController extends Controller {
  static targets = ["select"];

  connect() {
    const savedFont = localStorage.getItem("grylli-font") || "inter";

    setTimeout(() => {
      this.applyFont(savedFont);
      if (this.hasSelectTarget) {
        this.selectTarget.value = savedFont;
      }
    }, 10);
  }

  change(event) {
    const font = event.target.value;
    this.applyFont(font);
    localStorage.setItem("grylli-font", font);
  }

  applyFont(font) {
    document.fonts.ready.then(() => {
      const html = document.documentElement;
      const className = `font-${font}`;

      if (!FONT_CLASSES.includes(className)) {
        console.warn(`Unknown font: ${font}`);
        return;
      }

      // Apply new font class
      html.classList.remove(...Array.from(html.classList).filter(cls => cls.startsWith("font-")));
      html.classList.add(className);

      // Confirm font loaded (quietly)
      const testFamily = FONT_FAMILIES[font];
      if (testFamily) {
        document.fonts.load(`16px ${testFamily}`).catch(() => {});
      }

      // Trigger layout reflow
      const glyph = document.createElement("div");
      glyph.textContent = "Wg";
      glyph.style.fontFamily = testFamily;
      glyph.style.position = "absolute";
      glyph.style.visibility = "hidden";
      glyph.style.fontSize = "64px";
      document.body.appendChild(glyph);

      requestAnimationFrame(() => {
        glyph.offsetHeight;
        document.body.removeChild(glyph);
      });

      // Rerender trigger
      const originalSize = html.style.fontSize || "";
      html.style.fontSize = "101%";
      requestAnimationFrame(() => {
        html.style.fontSize = originalSize;
      });
    });
  }
}
