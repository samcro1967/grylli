// app/static/js/controllers/layout_debug_controller.js
import { Controller } from "../vendor/stimulus.js";

export default class extends Controller {
  static get targets() {
    return [
      "themeDebug", "viewportDebug", "layoutMetricsDebug", "localStorageDebug", "cookiesDebug",
      "performanceDebug", "userAgentDebug", "stimulusControllersDebug", "stimulusTargetsDebug",
      "eventListenersDebug", "ariaDebug", "focusedElementDebug", "scrollDebug", "sidebarDebug",
      "collapseDebug", "footerDebug", "sidebarDom", "headerDebug", "themeToggleDebug",
      "languageToggleDebug", "profileDropdownDebug", "footerDom", "computedStylesDebug",
      "scriptDebug", "styleDebug", "routeDebug", "formDebug", "memoryDebug",
      "visibilityDebug", "rawHtmlDebug"
    ];
  }

  static get optionalTargets() {
    return ["debugPageDropdown"];
  }

  connect() {
    console.log("✅ layout_debug_controller connected");

    const key = "__GrylliDebugPages";
    let pages = JSON.parse(localStorage.getItem(key) || "[]");

    const base = (window.BASE_URL || "").replace(/\/$/, "");

    // Remember to add debug block to template also
    const preloadPages = [
      { label: "List Users", url: `${base}/admin/users/` },
      { label: "List Emails", url: `${base}/email/overview/` },
      { label: "List Messages", url: `${base}/messages/overview/` },
      { label: "List Apprise", url: `${base}/messages/apprise/overview/` },
      { label: "List Webhook", url: `${base}/messages/webhook/overview/` },
      { label: "List Reminders", url: `${base}/reminders/overview/` },
      { label: "List User SMTP", url: `${base}/email/smtp/overview/` },
    ];

    const labelsToKeep = new Set(preloadPages.map(p => p.label));
    pages = preloadPages.concat(
      pages.filter(p => !labelsToKeep.has(p.label))
    );

    // 🔠 Sort AFTER merging preload pages
    pages.sort((a, b) => a.label.localeCompare(b.label));

    // Save back updated and sorted list
    localStorage.setItem(key, JSON.stringify(pages));

    requestAnimationFrame(() => {
      this._safe(() => {
        const select = document.querySelector("#debugPageDropdown");
        if (!select) return;

        // ✅ Fully clear all existing options (including ghost ones)
        select.options.length = 0;

        // ✅ Add default placeholder option
        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = "Choose a Page...";
        select.appendChild(defaultOption);

        // ✅ Use the same `pages` list as before
        const currentPath = window.location.pathname;
        const pages = JSON.parse(localStorage.getItem("__GrylliDebugPages") || "[]");

        pages.forEach(({ url, label }) => {
          if (url === currentPath) return;

          const option = document.createElement("option");
          option.value = url;
          option.textContent = label;
          select.appendChild(option);
        });

        // ✅ Safely handle selection
        select.addEventListener("change", () => {
          const selectedPath = select.value;
          const iframe = document.getElementById("debugPreviewIframe");

          if (!selectedPath || !iframe || selectedPath.startsWith(":")) {
            console.warn("🚫 Invalid debug selection:", selectedPath);
            return;
          }

          // Only basic URL safety check now
          if (!selectedPath.startsWith(base)) {
            console.warn("🚫 Unsafe debug URL rejected:", selectedPath);
            return;
          }

          iframe.src = selectedPath;
        });
      });
    });

    window.addEventListener("message", (event) => {
      if (event.data === "grylli:requestDebugExport") {
        this._safe(() => {
          const fields = this.constructor.targets;
          let output = "GRYLLI LAYOUT DEBUG REPORT\n===========================\n\n";

          fields.forEach(target => {
            const el = this[`${target}Target`];
            if (el && el.textContent) {
              const content = (target === "rawHtmlDebug" && el.textContent.length > 5000)
                ? "[Truncated HTML snapshot]\n"
                : el.textContent;
              output += `## ${this._formatTitle(target)}\n${content}\n\n`;
            }
          });

          event.source.postMessage({
            type: "grylli:debugExport",
            payload: output
          }, "*");
        });
      }
    });

    this._safe(() => this.logAllDebug());
  }

  exportIframe() {
    const iframe = document.getElementById("debugPreviewIframe");
    if (!iframe || !iframe.contentWindow) {
      alert("⚠️ No page loaded in the debug iframe yet.");
      return;
    }

    const iframeWindow = iframe.contentWindow;

    const listener = (event) => {
      if (event.data?.type === "grylli:debugExport") {
        const output = event.data.payload;
        const blob = new Blob([output], { type: "text/plain" });
        const url = URL.createObjectURL(blob);

        // ✅ Generate filename before anchor
        const selectedOption = document.querySelector("#debugPageDropdown")?.selectedOptions?.[0];
        const label = selectedOption?.textContent?.trim().replace(/\s+/g, "_").toLowerCase() || "debug_page";
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
        const filename = `grylli_${label}_${timestamp}.txt`;

        const a = document.createElement("a");
        a.href = url;
        a.download = filename;

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        window.removeEventListener("message", listener);

        // ✅ Trigger export request
        iframeWindow.postMessage("grylli:requestDebugExport", "*");

      }
    };

    window.addEventListener("message", listener);
    iframeWindow.postMessage("grylli:requestDebugExport", "*");
  }

  logAllDebug() {
    const html = document.documentElement;

    this._safe(() => {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      this.themeDebugTarget.textContent =
        `Theme: ${html.classList.contains("dark") ? "Dark" : "Light"}\n` +
        `<html> classes: ${[...html.classList].join(" ")}\n` +
        `System prefers dark: ${prefersDark}`;
    });

    this._safe(() => {
      this.viewportDebugTarget.textContent =
        `Viewport Width: ${window.innerWidth}px\nViewport Height: ${window.innerHeight}px`;
    });

    this._safe(() => {
      const sidebarMiddle = document.querySelector(".sidebar-middle");
      const main = document.querySelector("main");
      this.layoutMetricsDebugTarget.textContent =
        `Body Overflow: ${getComputedStyle(document.body).overflow}\n` +
        `Sidebar Scroll Height: ${sidebarMiddle?.scrollHeight || "N/A"}\n` +
        `Main Scroll Height: ${main?.scrollHeight || "N/A"}\n` +
        `Window ScrollY: ${window.scrollY}`;
    });

    this._safe(() => {
      this.localStorageDebugTarget.textContent =
        `Local Storage Keys:\n${Object.entries(localStorage).map(([k, v]) => `${k}: ${v}`).join("\n")}`;
    });

    this._safe(() => {
      this.cookiesDebugTarget.textContent = `Cookies: ${document.cookie}`;
    });

    this._safe(() => {
      const nav = performance.getEntriesByType("navigation")[0];
      this.performanceDebugTarget.textContent = nav
        ? JSON.stringify(nav.toJSON(), null, 2)
        : "Navigation timing not available.";
    });

    this._safe(() => {
      this.userAgentDebugTarget.textContent =
        `User Agent: ${navigator.userAgent}\nPath: ${window.location.pathname}`;
    });

    this._safe(() => {
      const controllers = Array.from(document.querySelectorAll("[data-controller]"))
        .map(el => el.getAttribute("data-controller")).join(", ");
      this.stimulusControllersDebugTarget.textContent = `Controllers:\n${controllers}`;
    });

    this._safe(() => {
      const targets = Array.from(document.querySelectorAll("[data-target]"))
        .map(el => el.getAttribute("data-target")).join(", ");
      this.stimulusTargetsDebugTarget.textContent = `Targets:\n${targets}`;
    });

    this._safe(() => {
      try {
        const registered = window.application?.controllers?.map(c => c.identifier) || [];
        this.stimulusControllersDebugTarget.textContent += `\n\nConnected:\n${registered.join(", ")}`;
      } catch (e) {
        this.stimulusControllersDebugTarget.textContent += "\n⚠️ Unable to fetch registered Stimulus controllers.";
      }
    });

    this.eventListenersDebugTarget.textContent =
      "Event Listeners: (Use browser DevTools to inspect live listeners)";

    this._safe(() => {
      this.ariaDebugTarget.textContent =
        `ARIA Roles:\n${Array.from(document.querySelectorAll("[role]"))
          .map(el => el.getAttribute("role")).join(", ")}`;
    });

    this._safe(() => {
      this.focusedElementDebugTarget.textContent =
        `Focused Element: ${document.activeElement?.tagName}`;
    });

    this._safe(() => {
      this.scrollDebugTarget.textContent =
        `document.body.scrollTop: ${document.body.scrollTop}\n` +
        `document.documentElement.scrollTop: ${document.documentElement.scrollTop}`;
    });

    this._safe(() => {
      const sidebarCtrl = document.querySelector('[data-controller="sidebar"]');
      const collapsed = JSON.parse(localStorage.getItem("sidebarCollapsed") || "false");
      this.sidebarDebugTarget.textContent = sidebarCtrl
        ? `Sidebar found. Collapsed: ${collapsed}`
        : "Sidebar not found.";
      this.sidebarDomTarget.textContent = sidebarCtrl?.outerHTML.slice(0, 3000) || "Sidebar not found.";
    });

    this._safe(() => {
      const collapseCount = document.querySelectorAll('[data-controller="collapse"]').length;
      this.collapseDebugTarget.textContent = `Collapse sections: ${collapseCount}`;
    });

    const footer = document.querySelector(".sidebar-footer");
    this.footerDebugTarget.textContent = footer
      ? `Sidebar footer height: ${footer.offsetHeight}px`
      : "Sidebar footer not found.";
    this.footerDomTarget.textContent = footer?.outerHTML.slice(0, 3000) || "Footer not found.";

    this._safe(() => {
      const header = document.querySelector("header");
      this.headerDebugTarget.textContent = header
        ? `Header height: ${header.offsetHeight}px\nClasses: ${header.className}`
        : "Header not found.";
    });

    this._safe(() => {
      const toggle = document.querySelector('[data-controller="theme"]');
      this.themeToggleDebugTarget.textContent = toggle
        ? `Theme toggle present. Stored: ${localStorage.getItem("theme") || "not set"}`
        : "Theme toggle not found.";
    });

    this._safe(() => {
      const lang = document.querySelector('[data-controller="lang"] select');
      this.languageToggleDebugTarget.textContent = lang
        ? `Language selected: ${lang.value}`
        : "Language selector not found.";
    });

    this._safe(() => {
      const btn = document.querySelector('[data-action~="profile#toggleDropdown"]');
      const dropdown = document.querySelector("#profile-dropdown");
      const visible = dropdown && dropdown.offsetParent !== null;
      this.profileDropdownDebugTarget.textContent =
        btn && dropdown
          ? `Profile dropdown visible: ${visible}`
          : "Profile toggle or dropdown not found.";
    });

    this._safe(() => {
      const sidebarCtrl = document.querySelector('[data-controller="sidebar"]');
      const keys = ["background-color", "width", "height", "display", "position"];
      const styles = sidebarCtrl ? getComputedStyle(sidebarCtrl) : null;
      this.computedStylesDebugTarget.textContent = styles
        ? keys.map(k => `${k}: ${styles.getPropertyValue(k)}`).join("\n")
        : "Sidebar not found for styles.";
    });

    this._safe(() => {
      this.scriptDebugTarget.textContent = Array.from(document.scripts).map(s =>
        `SRC: ${s.src || "[inline]"} | async=${s.async} | type=${s.type || "text/javascript"}`
      ).join("\n");
    });

    this._safe(() => {
      this.styleDebugTarget.textContent = Array.from(document.styleSheets)
        .map(sheet => sheet.href || "[inline or dynamic]").join("\n");
    });

    this._safe(() => {
      const formText = Array.from(document.forms).map((form, i) => {
        const inputs = Array.from(form.elements).map(input =>
          `- ${input.tagName.toLowerCase()}[type=${input.type || "text"} name=${input.name || "?"}]`
        );
        return `Form #${i + 1}:\n${inputs.join("\n")}`;
      }).join("\n\n") || "No forms found.";
      this.formDebugTarget.textContent = formText;

      if (document.forms.length === 0) {
        const formSection = this.formDebugTarget.closest("section");
        if (formSection) formSection.style.display = "none";
      }
    });

    this._safe(() => {
      const htmxAttrs = Array.from(document.querySelectorAll("[hx-get], [hx-post], [hx-target]"));
      const report = [`HTMX elements: ${htmxAttrs.length}`];
      htmxAttrs.forEach(el => {
        const tag = el.tagName.toLowerCase();
        const info = Array.from(el.attributes)
          .filter(attr => attr.name.startsWith("hx-"))
          .map(attr => `${attr.name}="${attr.value}"`)
          .join(" ");
        report.push(`- <${tag}> ${info}`);
      });
      this.eventListenersDebugTarget.textContent += `\n\n${report.join("\n")}`;
    });

    this._safe(() => {
      const check = sel => {
        const el = document.querySelector(sel);
        return el ? (el.offsetParent !== null ? "visible" : "hidden") : "not found";
      };
      this.visibilityDebugTarget.textContent =
        `Header: ${check("header")}\nSidebar: ${check('[data-controller="sidebar"]')}\nFooter: ${check(".sidebar-footer")}\nMain: ${check("main")}`;
    });

    this._safe(() => {
      if (performance.memory) {
        const { usedJSHeapSize, totalJSHeapSize } = performance.memory;
        this.memoryDebugTarget.textContent =
          `Used: ${(usedJSHeapSize / 1048576).toFixed(1)} MB\nTotal: ${(totalJSHeapSize / 1048576).toFixed(1)} MB`;
      } else {
        this.memoryDebugTarget.textContent = "Memory info not supported.";
      }
    });

    this._safe(() => {
      const ctx = window.__GrylliContext || {};
      this.routeDebugTarget.textContent =
        `Route: ${ctx.route || window.location.pathname}\n` +
        `Title: ${document.title}\n` +
        `View: ${ctx.view || "Unknown"}\n` +
        `Template: ${ctx.template || "Unknown"}`;
    });

    this._safe(() => {
      const html = document.documentElement.outerHTML;
      const safeText = html.length > 5000
        ? html.slice(0, 5000) + "\n[...truncated]"
        : html;

      const pre = document.createElement("pre");
      pre.textContent = safeText;

      this.rawHtmlDebugTarget.replaceChildren(pre);
    });

    // Customization summary: theme, contrast, font, tracking, line height
    this._safe(() => {
      const html = document.documentElement;
      const styleData = [
        `Theme: ${html.getAttribute("data-theme") || "unknown"}`,
        `Contrast: ${html.dataset.contrast || "default"}`,
        `Tracking: ${html.dataset.tracking || "default"}`,
        `Line Height: ${html.dataset.lineHeight || "default"}`,
        `Font Family: ${getComputedStyle(document.body).fontFamily}`,
      ];
      this.themeDebugTarget.textContent += `\n${styleData.join("\n")}`;
    });

  }

  _safe(fn) {
    try { fn(); } catch (e) { console.warn("⛔️ Debug block failed:", e); }
  }

  clearAllDebug() {
    localStorage.clear();
    document.cookie.split(";").forEach(cookie => {
      const name = cookie.split("=")[0].trim();
      document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
    });
    window.location.reload();
  }

  exportDebug() {
    const fields = this.constructor.targets;
    let output = "GRYLLI LAYOUT DEBUG REPORT\n===========================\n\n";
    fields.forEach(target => {
      const el = this[`${target}Target`];
      if (el && el.textContent) {
        const content = (target === "rawHtmlDebug" && el.textContent.length > 5000)
          ? "[Truncated HTML snapshot]\n"
          : el.textContent;
        output += `## ${this._formatTitle(target)}\n${content}\n\n`;
      }
    });

    const blob = new Blob([output], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "grylli_layout_debug.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  _formatTitle(key) {
    return key
      .replace(/([A-Z])/g, " $1")
      .replace(/Debug$/, "")
      .replace(/Dom/g, "DOM")
      .replace(/Css/g, "CSS")
      .replace(/^./, str => str.toUpperCase());
  }
}
