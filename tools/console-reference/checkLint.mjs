import { ESLint } from "eslint";
import fs from "node:fs";
const engine = new ESLint({ fix: process.argv.includes("--fix") });
const all = process.argv.includes("--all");
const results = await engine.lintFiles([
  all ? "apps/web/src" : "apps/web/src/features/example-console",
]);
if (process.argv.includes("--fix")) await ESLint.outputFixes(results);
const output = "scratch/console-reference-recovery";
fs.mkdirSync(output, { recursive: true });
const scope = all ? "all" : "examples";
const serialized = JSON.stringify(results, null, 2);
const stamp = new Date().toISOString().replaceAll(/[:.]/g, "-");
fs.writeFileSync(`${output}/lint-${scope}-${stamp}.json`, serialized);
fs.writeFileSync(`${output}/lint-${scope}-latest.json`, serialized);
if (!all) fs.writeFileSync("scratch/console-reference/lint-diagnostics.json", serialized);
const counts = {};
for (const result of results)
  for (const m of result.messages) counts[m.ruleId] = (counts[m.ruleId] ?? 0) + 1;
console.log(JSON.stringify(counts, null, 2));
console.log(
  "files",
  results.length,
  "errors",
  results.reduce((n, r) => n + r.errorCount, 0),
  "warnings",
  results.reduce((n, r) => n + r.warningCount, 0),
);
process.exitCode = results.some((r) => r.errorCount > 0 || r.warningCount > 0) ? 1 : 0;
