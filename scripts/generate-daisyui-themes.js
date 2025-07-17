const fs = require("fs");
const path = require("path");
const config = require("../tailwind.config.js");

const themes = config.daisyui?.themes || [];

// Sort themes alphabetically (case-insensitive)
const sortedThemes = themes.slice().sort((a, b) => {
  if (typeof a === "string" && typeof b === "string") {
    return a.toLowerCase().localeCompare(b.toLowerCase());
  }
  // If themes are objects or mixed, handle accordingly here if needed
  return 0;
});

const outputPath = path.resolve(__dirname, "../app/static/daisyui-themes.json");

fs.writeFileSync(outputPath, JSON.stringify(sortedThemes, null, 2));

console.log(`Wrote ${sortedThemes.length} themes to ${outputPath}`);
