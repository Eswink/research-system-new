import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execFileSync } from "node:child_process";

// Recovery evidence only. Never traverses credentials, caches or external paths.
const root = fs.realpathSync(".");
const output = path.join(root, "scratch/console-reference-recovery");
const snapshot = path.join(output, "baseline");
const roots = ["apps/web/src", "apps/web/tests", "tools/console-reference"];
const ignored = new Set([".mimosa", "node_modules", "dist"]);

function digest(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function capture(directory, manifest) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.isSymbolicLink() || ignored.has(entry.name)) continue;
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      capture(file, manifest);
    } else if (entry.isFile()) {
      const relative = path.relative(root, file);
      const target = path.join(snapshot, relative);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.copyFileSync(file, target, fs.constants.COPYFILE_EXCL);
      manifest[relative.replaceAll(path.sep, "/")] = digest(file);
    }
  }
}

if (fs.existsSync(snapshot)) throw new Error("Baseline already exists; refusing overwrite");
fs.mkdirSync(output, { recursive: true });
const protectedPaths = JSON.parse(
  fs.readFileSync("scratch/console-reference/protected-paths.json", "utf8"),
);
const protectedReport = Object.fromEntries(
  Object.entries(protectedPaths).map(([file, expected]) => [
    file,
    {
      expected,
      actual: digest(file),
      unchanged: digest(file) === expected,
    },
  ]),
);
const manifest = {};
for (const directory of roots) capture(path.join(root, directory), manifest);
fs.writeFileSync(path.join(output, "baseline-manifest.json"), JSON.stringify(manifest, null, 2));
fs.writeFileSync(
  path.join(output, "protected-baseline.json"),
  JSON.stringify(protectedReport, null, 2),
);
fs.writeFileSync(
  path.join(output, "git-status-before.txt"),
  execFileSync("git", ["status", "--short"]),
);
console.log(JSON.stringify({ files: Object.keys(manifest).length, protectedReport }, null, 2));
