import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const cfg = ts.getParsedCommandLineOfConfigFile(
  path.resolve("apps/web/tsconfig.json"),
  {},
  {
    ...ts.sys,
    onUnRecoverableConfigFileDiagnostic: (d) => {
      throw new Error(String(d.messageText));
    },
  },
);
const program = ts.createProgram(cfg.fileNames, cfg.options);
const checker = program.getTypeChecker();
let count = 0;
for (const sf of program.getSourceFiles()) {
  if (!sf.fileName.includes("/features/example-console/") || !sf.fileName.endsWith(".tsx"))
    continue;
  const edits = [];
  function visit(node) {
    if (ts.isTemplateExpression(node))
      for (const span of node.templateSpans) {
        const expr = span.expression;
        const type = checker.getTypeAtLocation(expr);
        const types = type.isUnion() ? type.types : [type];
        if (types.every((t) => (t.flags & ts.TypeFlags.StringLike) !== 0)) continue;
        const text = expr.getText(sf);
        const css = /^visual\.[\w]+$/.test(text);
        const replacement = css ? `(${text} ?? "")` : `String(${text})`;
        edits.push({ start: expr.getStart(sf), end: expr.end, text: replacement });
      }
    ts.forEachChild(node, visit);
  }
  visit(sf);
  // Process leaf-most first; an outer template interpolation may itself contain a template.
  const nonOverlapping = edits.filter(
    (a) => !edits.some((b) => b !== a && b.start >= a.start && b.end <= a.end),
  );
  let content = sf.text;
  for (const e of nonOverlapping.sort((a, b) => b.start - a.start))
    content = content.slice(0, e.start) + e.text + content.slice(e.end);
  if (nonOverlapping.length) fs.writeFileSync(sf.fileName, content, "utf8");
  count += nonOverlapping.length;
}
console.log("Explicit display conversions:", count);
