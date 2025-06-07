document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("themeToggle");
  const knob = document.getElementById("themeToggleKnob");

  function setTheme(isDark) {
    if (isDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }

  // Initialize theme
  const isDark = localStorage.getItem("theme") === "dark";
  setTheme(isDark);

  // Only attach event if toggle element exists
  if (toggle) {
    toggle.addEventListener("click", () => {
      const currentlyDark = document.documentElement.classList.contains("dark");
      setTheme(!currentlyDark);
    });
  }

  // Optional: add logic for `knob` if you're using it
  if (knob) {
    // Example: sync knob position or animation
  }
});
