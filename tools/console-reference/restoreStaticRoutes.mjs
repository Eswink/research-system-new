import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const targets = [
  "apps/web/src/App.tsx",
  "apps/web/src/navigation/PageRenderer.tsx",
  "apps/web/src/features/example-console/ExamplePage.tsx",
  "apps/web/src/features/example-console/ExampleConsole.tsx",
];

// Repository policy rejects ImportExpression. Keep separate render trees without
// bypassing that rule; production Vite bundles static imports without dev module waterfalls.
for (const file of targets) {
  let source = fs.readFileSync(file, "utf8");
  const parsed = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const edits = [];
  const imports = [];
  for (const statement of parsed.statements) {
    if (!ts.isVariableStatement(statement)) continue;
    const declaration = statement.declarationList.declarations[0];
    if (!declaration?.initializer || !ts.isCallExpression(declaration.initializer)) continue;
    if (declaration.initializer.expression.getText(parsed) !== "lazy") continue;
    const text = statement.getText(parsed);
    const match = text.match(/import\("([^"]+)"\)/);
    if (!match) throw new Error(`Unsupported lazy declaration: ${file}`);
    imports.push(`import { ${declaration.name.getText(parsed)} } from "${match[1]}";`);
    edits.push({ start: statement.getStart(parsed), end: statement.end });
  }
  for (const edit of edits.sort((a, b) => b.start - a.start)) {
    source = source.slice(0, edit.start) + source.slice(edit.end);
  }
  source = source.replace(/import \{ lazy, Suspense/g, "import { Suspense");
  if (imports.length) fs.writeFileSync(file, imports.join("\n") + "\n" + source, "utf8");
  console.log(file, imports.length, "static component imports");
}
