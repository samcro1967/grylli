// layout.js
document.addEventListener("DOMContentLoaded", () => {
  // Clear flash messages after 5 seconds
  setTimeout(() => {
    const container = document.getElementById("toast-container");
    if (container) container.innerHTML = "";
  }, 5000);

  // Set global roleChangeBase if role-modal logic requires it
  window.roleChangeBase = document.body.dataset.roleChangeBase;
});
