/** Replace compiler-expanded fixture shapes only when the checker proves mutual assignability. */
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
    onUnRecoverableConfigFileDiagnostic: (diagnostic) => {
      throw new Error(String(diagnostic.messageText));
    },
  },
);
const program = ts.createProgram(cfg.fileNames, cfg.options);
const checker = program.getTypeChecker();
const registry = program.getSourceFile(
  path.resolve("apps/web/src/features/example-console/fixtureTypes.ts"),
);
const aliases = registry.statements.filter(ts.isTypeAliasDeclaration).map((statement) => ({
  name: statement.name.text,
  type: checker.getTypeFromTypeNode(statement.type),
}));

function signature(type) {
  return checker
    .getPropertiesOfType(type)
    .map((property) => property.name)
    .sort()
    .join("|");
}

function match(type) {
  const names = signature(type);
  if (!names) return null;
  return aliases.find(
    (alias) =>
      signature(alias.type) === names &&
      checker.isTypeAssignableTo(type, alias.type) &&
      checker.isTypeAssignableTo(alias.type, type),
  );
}

const log = [];
for (const source of program.getSourceFiles()) {
  const file = source.fileName.replaceAll("\\", "/");
  if (!file.includes("/features/example-console/reference/") || !file.endsWith(".tsx")) continue;
  const edits = [];
  function visit(node) {
    if (ts.isTypeNode(node) && node.getText(source).length > 240) {
      const type = checker.getTypeFromTypeNode(node);
      const parts = type.isUnion() ? type.types : [type];
      const nullish = parts.filter(
        (part) => part.flags & (ts.TypeFlags.Undefined | ts.TypeFlags.Null),
      );
      const value = checker.getNonNullableType(type);
      const array = checker.isArrayType(value);
      const inner = array ? checker.getElementTypeOfArrayType(value) : value;
      const alias = match(inner);
      if (alias) {
        const suffix = nullish.map((part) => checker.typeToString(part)).join(" | ");
        const text = `FixtureTypes.${alias.name}${array ? "[]" : ""}${suffix ? ` | ${suffix}` : ""}`;
        edits.push({ start: node.getStart(source), end: node.end, text });
        return;
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
  if (edits.length === 0) continue;
  let text = source.text;
  for (const edit of edits.sort((a, b) => b.start - a.start)) {
    text = text.slice(0, edit.start) + edit.text + text.slice(edit.end);
  }
  let relative = path
    .relative(path.dirname(file), registry.fileName)
    .replaceAll("\\", "/")
    .replace(/\.ts$/, "");
  if (!relative.startsWith(".")) relative = "./" + relative;
  if (!text.includes("import type * as FixtureTypes")) {
    text = `import type * as FixtureTypes from ${JSON.stringify(relative)};\n` + text;
  }
  fs.writeFileSync(file, text, "utf8");
  log.push({
    file,
    replacements: edits.length,
    removedCharacters: source.text.length - text.length,
  });
}
fs.writeFileSync(
  "scratch/console-reference-continuation/type-simplifications.json",
  JSON.stringify(log, null, 2),
);
console.log(
  "Fixture contract simplifications:",
  log.length,
  "modules;",
  log.reduce((sum, item) => sum + item.removedCharacters, 0),
  "characters removed",
);
