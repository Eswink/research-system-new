import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(path.resolve("apps/web/package.json"));
const prettier = require("prettier");
const root = "apps/web/src";
function files(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    if (entry.isSymbolicLink() || entry.name === ".mimosa" || entry.name === "node_modules")
      return [];
    const file = path.join(directory, entry.name);
    return entry.isDirectory() ? files(file) : /\.(ts|tsx|css)$/.test(file) ? [file] : [];
  });
}
const changed = [];
for (const file of files(root)) {
  const source = fs.readFileSync(file, "utf8");
  const options = await prettier.resolveConfig(file);
  const result = await prettier.format(source, { ...options, filepath: file });
  if (result !== source) {
    fs.writeFileSync(file, result, "utf8");
    changed.push(file);
  }
}
const output = "scratch/console-reference-recovery";
fs.mkdirSync(output, { recursive: true });
const stamp = new Date().toISOString().replaceAll(/[:.]/g, "-");
fs.writeFileSync(`${output}/formatted-${stamp}.json`, JSON.stringify(changed, null, 2));
console.log(
  "Formatted",
  changed.length,
  "source/style modules; fixtures and protected paths excluded",
);
