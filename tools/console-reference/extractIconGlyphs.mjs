import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import * as prettier from "prettier";
const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const root = "apps/web/src/features/example-console/reference";
for (const stem of ["Icon", "PECustomIcon"]) {
  const file = path.join(root, stem + ".tsx"),
    text = fs.readFileSync(file, "utf8");
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  let switchNode;
  function find(n) {
    if (ts.isSwitchStatement(n)) switchNode = n;
    ts.forEachChild(n, find);
  }
  find(sf);
  if (!switchNode) continue;
  const entries = [];
  for (const clause of switchNode.caseBlock.clauses) {
    if (!ts.isCaseClause(clause)) continue;
    let returned = clause.statements.find(ts.isReturnStatement)?.expression;
    while (returned && ts.isParenthesizedExpression(returned)) returned = returned.expression;
    if (!returned || !ts.isJsxElement(returned)) throw new Error("Non-SVG case " + stem);
    const content = returned.children.map((n) => n.getText(sf)).join("");
    entries.push(`[${clause.expression.getText(sf)}, <>${content}</>]`);
  }
  const glyphStem = stem === "Icon" ? "iconGlyphs" : "protocolIconGlyphs";
  let glyphs = `import type { ReactNode } from "react";\n\n/** Frozen design paths; no runtime dispatch or generated markup. */\nexport const glyphs: ReadonlyMap<string, ReactNode> = new Map<string, ReactNode>([\n${entries.join(",\n")}\n]);\n`;
  glyphs = await prettier.format(glyphs, {
    filepath: path.join(root, glyphStem + ".tsx"),
    printWidth: 100,
  });
  fs.writeFileSync(path.join(root, glyphStem + ".tsx"), glyphs, "utf8");
  const dimension = stem === "Icon" ? 12 : 10;
  let component = `import type { CSSProperties } from "react";\nimport { glyphs } from "./${glyphStem}";\n\ninterface Props { name?: string | undefined; size?: number; style?: CSSProperties | undefined; className?: string | undefined; }\n\n/** Shared SVG attributes; unknown design icon names remain visible as a neutral outline. */\nexport function ${stem}({ name, size = ${dimension}, style, className }: Props) {\n const shape = glyphs.get(name ?? "") ?? <circle cx="6" cy="6" r="4" />;\n const effectiveStyle = name === "spin" ? { ...style, animation: "spin 1s linear infinite" } : style;\n return <svg width={size} height={size} viewBox="0 0 ${dimension} ${dimension}" fill="none" stroke="currentColor"\n strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" className={className}\n style={effectiveStyle} aria-hidden="true">{shape}</svg>;\n}\n`;
  component = await prettier.format(component, { filepath: file, printWidth: 100 });
  fs.writeFileSync(file, component, "utf8");
  console.log(stem, entries.length, "glyphs extracted");
}
