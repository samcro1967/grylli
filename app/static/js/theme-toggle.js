// ---------------------------------------------------------------------
// theme-toggle.js
// Handles light/dark mode toggle and persistence via localStorage
// ---------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
  const themeToggleBtn = document.getElementById("themeToggle");
  const html = document.documentElement;

  // -------------------------------------------------------------------
  // Load and apply saved theme preference
  // -------------------------------------------------------------------
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "dark") {
    html.classList.add("dark");
  } else if (savedTheme === "light") {
    html.classList.remove("dark");
  } else {
    // DEFAULT TO DARK MODE ON FIRST VISIT
    html.classList.add("dark");
  }

  // -------------------------------------------------------------------
  // Toggle theme and persist to localStorage
  // -------------------------------------------------------------------
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", function () {
      html.classList.toggle("dark");

      console.log("Toggled dark class:", html.classList.contains("dark"));

      const isDark = html.classList.contains("dark");
      localStorage.setItem("theme", isDark ? "dark" : "light");
    });
  }
});
