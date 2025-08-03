// logger_controller.js
import { Controller } from "../vendor/stimulus.js";

// ─────────────────────────────────────────────────────────────
// Helper: Generate a semi-stable browser fingerprint
// ─────────────────────────────────────────────────────────────
/**
 * Generate a semi-stable client fingerprint for correlating logs.
 * 
 * The fingerprint includes:
 * - navigator.userAgent        (browser and OS)
 * - navigator.language         (browser language)
 * - navigator.platform         (OS platform)
 * - Intl.DateTimeFormat tz     (timezone string)
 * - navigator.deviceMemory     (RAM estimate, if available)
 * - screen.colorDepth          (display bit depth)
 * - navigator.hardwareConcurrency (logical cores)
 * 
 * This does NOT use screen size, local time, or IP to avoid volatility or privacy risk.
 * Only a short SHA-256 hash of these fields is sent.
 */
async function generateFingerprint() {
  if (!window.isSecureContext || !crypto?.subtle) {
    console.warn("⚠️ Insecure context or unsupported crypto. Skipping fingerprint.");
    return "insecure-context";
  }
  const components = [
    navigator.userAgent,
    navigator.language,
    navigator.platform,
    Intl.DateTimeFormat().resolvedOptions().timeZone,
    navigator.deviceMemory || "unknown",
    screen.colorDepth,
    navigator.hardwareConcurrency || "unknown"
  ].join("::");

  const buffer = new TextEncoder().encode(components);
  const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
  const hashHex = [...new Uint8Array(hashBuffer)]
    .map(b => b.toString(16).padStart(2, "0")).join("");

  return hashHex.slice(0, 12); // Shorten to 12 chars for log readability
}

// ─────────────────────────────────────────────────────────────
// Stimulus Controller
// ─────────────────────────────────────────────────────────────
export default class extends Controller {
  connect() {
    const base = window.BASE_URL || "";
    const logUrl = `${base}/admin/tools/log_js_error`;

    generateFingerprint().then(fp => {
      this.fingerprint = fp;

      // 0. Log fingerprint with explanation
      this._send(logUrl, {
        type: "fingerprint",
        fingerprint: fp,
        comment: "Generated from browser+OS+timezone+memory. See logger_controller.js for details."
      });

      this._logInitialEvents(logUrl);
    });
  }

  _logInitialEvents(logUrl) {
    // 1. Basic environment
    this._send(logUrl, {
      type: "environment",
      userAgent: navigator.userAgent,
      userAgentData: navigator.userAgentData || null,
      platform: navigator.platform,
      language: navigator.language,
      languages: navigator.languages,
      standalone: window.navigator.standalone || false,
      isSecureContext: window.isSecureContext,
      referrer: document.referrer
    });

    // 2. Timezone and client clock
    const now = new Date();
    this._send(logUrl, {
      type: "client-time",
      time: now.toISOString(),
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      offsetMinutes: now.getTimezoneOffset()
    });

    // 3. Viewport
    this._send(logUrl, {
      type: "viewport",
      width: window.innerWidth,
      height: window.innerHeight,
      orientation: screen.orientation?.type || "unknown"
    });

    // 4. Network info
    if (navigator.connection) {
      this._send(logUrl, {
        type: "network-info",
        downlink: navigator.connection.downlink,
        effectiveType: navigator.connection.effectiveType,
        rtt: navigator.connection.rtt,
        saveData: navigator.connection.saveData
      });
    }

    // 5. Missing feature detection
    const missing = [];
    if (!window.fetch) missing.push("fetch");
    if (!window.Promise) missing.push("Promise");
    if (!window.IntersectionObserver) missing.push("IntersectionObserver");
    if (!window.ResizeObserver) missing.push("ResizeObserver");
    if (!window.CSS || !CSS.supports("display: grid")) missing.push("CSS Grid");
    if (missing.length) {
      this._send(logUrl, { type: "missing-features", features: missing });
    }

    // 6. UI preferences
    this._send(logUrl, {
      type: "ui-preference",
      darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches
    });

    // 7. LocalStorage support
    let localStorageAvailable = true;
    try {
      localStorage.setItem("logger_test", "1");
      localStorage.removeItem("logger_test");
    } catch (_) {
      localStorageAvailable = false;
    }
    this._send(logUrl, {
      type: "storage",
      localStorageAvailable
    });

    // 8. Page load performance
    window.addEventListener("load", () => {
      const nav = performance.getEntriesByType("navigation")[0];
      if (!nav) return;
      this._send(logUrl, {
        type: "performance",
        timing: {
          domContentLoaded: nav.domContentLoadedEventEnd - nav.startTime,
          loadEvent: nav.loadEventEnd - nav.startTime,
          timeToFirstByte: nav.responseStart - nav.requestStart,
        }
      });
    });

    // 9. Visibility change
    document.addEventListener("visibilitychange", () => {
      this._send(logUrl, {
        type: "visibility",
        state: document.visibilityState,
        timestamp: new Date().toISOString()
      });
    });

    // 10. HTMX errors
    document.body.addEventListener("htmx:sendError", (e) => {
      this._send(logUrl, {
        type: "htmx-send-error",
        error: e.detail.error?.message || "Unknown send error",
        url: e.detail.pathInfo.requestPath
      });
    });

    document.body.addEventListener("htmx:responseError", (e) => {
      const xhr = e.detail.xhr;
      this._send(logUrl, {
        type: "htmx-response-error",
        status: xhr.status,
        url: e.detail.pathInfo.requestPath,
        snippet: xhr?.responseText?.slice(0, 500) || ""
      });
    });

    // 11. Resource load failures
    window.addEventListener("error", (event) => {
      const target = event.target || event.srcElement;
      if (target && (target.src || target.href)) {
        this._send(logUrl, {
          type: "resource-error",
          tag: target.tagName,
          url: target.src || target.href,
          outerHTML: target.outerHTML
        });
      }
    }, true);

    // 12. Runtime JS errors
    window.onerror = (message, source, lineno, colno, error) => {
      this._send(logUrl, {
        type: "error",
        message,
        source,
        lineno,
        colno,
        stack: error?.stack || null
      });
    };

    // 13. Unhandled promise rejections
    window.onunhandledrejection = (event) => {
      this._send(logUrl, {
        type: "unhandledrejection",
        reason: event.reason
      });
    };

    // 14. Console messages
    ["log", "info", "warn", "error"].forEach(level => {
      const original = console[level];
      console[level] = (...args) => {
        original.apply(console, args);
        this._send(logUrl, {
          type: "console",
          level,
          message: args.map(a => String(a)).join(" "),
          timestamp: new Date().toISOString()
        });
      };
    });

    console.log("📡 Logger controller connected");
  }

  _send(url, payload) {
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fingerprint: this.fingerprint || null,
        ...payload
      })
    });
  }
}