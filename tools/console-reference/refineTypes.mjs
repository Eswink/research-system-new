import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const root = process.argv[2] ?? "apps/web/src/features/example-console/reference";
const numerics = new Set([
  "rules.length",
  "selected.consequence.affected_tasks",
  "warnCount",
  "infoCount",
  "errorCount",
  "downstream.length",
  "confirmDelete?.runs || 0",
]);
for (const name of fs.readdirSync(root).filter((n) => /\.tsx?$/.test(n))) {
  const file = path.join(root, name);
  let s = fs.readFileSync(file, "utf8");
  const sf = ts.createSourceFile(file, s, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const edits = [];
  function walk(n) {
    if (
      ts.isPropertyAccessExpression(n) &&
      n.name.text === "map" &&
      ts.isArrayLiteralExpression(n.expression) &&
      n.expression.elements.some(ts.isArrayLiteralExpression)
    )
      edits.push({
        start: n.expression.getStart(sf),
        end: n.expression.end,
        text: `(${n.expression.getText(sf)} as const)`,
      });
    if (
      ts.isCallExpression(n) &&
      ts.isPropertyAccessExpression(n.expression) &&
      n.expression.name.text === "replace" &&
      n.arguments[1] &&
      numerics.has(n.arguments[1].getText(sf))
    ) {
      const a = n.arguments[1];
      edits.push({ start: a.getStart(sf), end: a.end, text: `String(${a.getText(sf)})` });
    }
    ts.forEachChild(n, walk);
  }
  walk(sf);
  edits.sort((a, b) => b.start - a.start);
  for (const e of edits) s = s.slice(0, e.start) + e.text + s.slice(e.end);
  fs.writeFileSync(file, s, "utf8");
}
console.log("Preserved tuple element semantics and explicit numeric text conversions");
