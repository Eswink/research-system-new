/** Reuse imported DTOs and hook return contracts instead of duplicating inferred state structures. */
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

function names(type) {
  return checker
    .getPropertiesOfType(type)
    .map((property) => property.name)
    .sort()
    .join("|");
}

function contracts(source) {
  const result = [];
  for (const statement of source.statements) {
    if (!ts.isImportDeclaration(statement)) continue;
    const bindings = statement.importClause?.namedBindings;
    if (!bindings || !ts.isNamedImports(bindings)) continue;
    for (const binding of bindings.elements) {
      const alias = checker.getSymbolAtLocation(binding.name);
      if (!alias) continue;
      const symbol = checker.getAliasedSymbol(alias);
      const id = binding.name.text;
      if (symbol.flags & (ts.SymbolFlags.Interface | ts.SymbolFlags.TypeAlias)) {
        const type = checker.getDeclaredTypeOfSymbol(symbol);
        if (!type.typeParameters?.length && !type.aliasTypeArguments?.length && names(type)) {
          result.push({ type, text: id });
        }
      }
      if (!id.startsWith("use")) continue;
      const signature = checker.getTypeAtLocation(binding.name).getCallSignatures()[0];
      if (signature && !signature.typeParameters?.length) {
        result.push({ type: signature.getReturnType(), text: `ReturnType<typeof ${id}>` });
      }
    }
  }
  return result;
}

const log = [];
for (const source of program.getSourceFiles()) {
  const file = source.fileName.replaceAll("\\", "/");
  if (!file.includes("/apps/web/src/") || !file.endsWith(".tsx")) continue;
  const known = contracts(source);
  if (!known.length) continue;
  const edits = [];
  function visit(node) {
    if (ts.isPropertySignature(node) && node.type && node.type.getText(source).length > 240) {
      const type = checker.getTypeFromTypeNode(node.type);
      const contract = known.find(
        (item) =>
          names(type) &&
          names(type) === names(item.type) &&
          checker.isTypeAssignableTo(type, item.type) &&
          checker.isTypeAssignableTo(item.type, type),
      );
      if (contract) {
        edits.push({ start: node.type.getStart(source), end: node.type.end, text: contract.text });
        return;
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
  if (!edits.length) continue;
  let text = source.text;
  for (const edit of edits.sort((a, b) => b.start - a.start)) {
    text = text.slice(0, edit.start) + edit.text + text.slice(edit.end);
  }
  fs.writeFileSync(file, text, "utf8");
  log.push({
    file,
    replacements: edits.length,
    removedCharacters: source.text.length - text.length,
  });
}
fs.writeFileSync(
  "scratch/console-reference-continuation/view-contracts.json",
  JSON.stringify(log, null, 2),
);
console.log("Simplified view contracts:", log.length, "modules");
