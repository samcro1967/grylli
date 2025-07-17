// app/static/js/collapse_state_loader.js

(() => {
  try {
    for (const [key, value] of Object.entries(localStorage)) {
      if (key.startsWith("collapse-state-")) {
        const id = key.replace("collapse-state-", "");
        const open = value === "true";
        document.documentElement.classList.add(open ? `expand-${id}` : `collapse-${id}`);
      }
    }
  } catch (_) {}
})();
