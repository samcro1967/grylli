const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

const pkgLockPath = path.resolve(__dirname, '../package-lock.json');
const outputPath = path.resolve(__dirname, '../app/static/version.json');

const pkgLock = JSON.parse(fs.readFileSync(pkgLockPath, 'utf-8'));

const versions = {
  "Node.js": execSync('node -v').toString().trim(),
  "npm": execSync('npm -v').toString().trim(),
};

const depsToCheck = [
  { key: 'Tailwind CSS', package: 'tailwindcss' },
  { key: 'PostCSS', package: 'postcss' },
  { key: 'Autoprefixer', package: 'autoprefixer' },
  { key: 'DaisyUI', package: 'daisyui' },
];

depsToCheck.forEach(({ key, package: pkgName }) => {
  if (pkgLock.packages && pkgLock.packages[`node_modules/${pkgName}`]) {
    versions[key] = pkgLock.packages[`node_modules/${pkgName}`].version;
  } else if (pkgLock.dependencies && pkgLock.dependencies[pkgName]) {
    versions[key] = pkgLock.dependencies[pkgName].version;
  } else {
    versions[key] = 'not found';
  }
});

fs.writeFileSync(outputPath, JSON.stringify(versions, null, 2));
console.log('✅ Frontend versions written to', outputPath);
