/** Restore editable page-local state for handoff controls; never calls a business API. */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const root = path.resolve("apps/web/src/features/example-console/reference");
const report = [];

function files(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(directory, entry.name);
    return entry.isDirectory() ? files(file) : file.endsWith(".tsx") ? [file] : [];
  });
}

function emptyHandler(attribute) {
  if (!attribute.initializer || !ts.isJsxExpression(attribute.initializer)) return false;
  const expression = attribute.initializer.expression;
  return (
    expression &&
    ts.isArrowFunction(expression) &&
    ts.isBlock(expression.body) &&
    expression.body.statements.length === 0
  );
}

function ownerOf(node) {
  let parent = node.parent;
  while (parent) {
    if (
      ts.isFunctionDeclaration(parent) ||
      ts.isArrowFunction(parent) ||
      ts.isFunctionExpression(parent)
    )
      return parent;
    parent = parent.parent;
  }
  return undefined;
}

function componentName(owner) {
  if (owner.name && ts.isIdentifier(owner.name)) return owner.name.text;
  if (ts.isVariableDeclaration(owner.parent) && ts.isIdentifier(owner.parent.name)) {
    return owner.parent.name.text;
  }
  return "";
}

function initialValue(attribute, source) {
  const initial = attribute.initializer;
  if (!initial) return undefined;
  if (ts.isStringLiteral(initial)) return JSON.stringify(initial.text);
  if (ts.isJsxExpression(initial) && initial.expression) {
    return initial.expression.getText(source);
  }
  return undefined;
}

function inspect(file) {
  const text = fs.readFileSync(file, "utf8");
  const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const replacements = [];
  const declarations = new Map();
  let counter = 0;
  function visit(node) {
    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      const tag = node.tagName.getText(source);
      if (["Select", "TextInput", "TagInput"].includes(tag)) {
        const attributes = node.attributes.properties.filter(ts.isJsxAttribute);
        const handler = attributes.find((item) => item.name.getText(source) === "onChange");
        const value = attributes.find(
          (item) => item.name.getText(source) === (tag === "TagInput" ? "tags" : "value"),
        );
        const owner = ownerOf(node);
        if (
          handler &&
          value &&
          emptyHandler(handler) &&
          owner &&
          ts.isBlock(owner.body) &&
          /^[A-Z]/.test(componentName(owner))
        ) {
          const initial = initialValue(value, source);
          if (initial !== undefined) {
            let name;
            do {
              name = `example${tag === "TagInput" ? "Tags" : "Field"}${String(++counter)}`;
            } while (text.includes(name));
            const setter = `set${name[0].toUpperCase()}${name.slice(1)}`;
            const declaration = `\n  const [${name}, ${setter}] = useState(${initial});`;
            const offset = owner.body.getStart(source) + 1;
            declarations.set(offset, (declarations.get(offset) ?? "") + declaration);
            replacements.push({
              start: value.initializer.getStart(source),
              end: value.initializer.end,
              text: `{${name}}`,
            });
            replacements.push({
              start: handler.initializer.getStart(source),
              end: handler.initializer.end,
              text: `{${setter}}`,
            });
            report.push({
              file: path.relative(root, file),
              component: componentName(owner),
              control: tag,
              initial,
            });
          }
        }
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
  if (!replacements.length) return;
  for (const [start, content] of declarations)
    replacements.push({ start, end: start, text: content });
  let output = text;
  for (const edit of replacements.sort((a, b) => b.start - a.start)) {
    output = output.slice(0, edit.start) + edit.text + output.slice(edit.end);
  }
  const hasState = source.statements.filter(ts.isImportDeclaration).some((statement) => {
    const bindings = statement.importClause?.namedBindings;
    return (
      statement.moduleSpecifier.text === "react" &&
      bindings &&
      ts.isNamedImports(bindings) &&
      bindings.elements.some((element) => element.name.text === "useState")
    );
  });
  if (!hasState) output = `import { useState } from "react";\n${output}`;
  const parsed = ts.createSourceFile(file, output, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  if (parsed.parseDiagnostics.length) throw new Error(`Refused invalid edit: ${file}`);
  fs.writeFileSync(file, output, "utf8");
}

for (const file of files(root)) inspect(file);
const destination = "scratch/console-reference-continuation";
fs.mkdirSync(destination, { recursive: true });
fs.writeFileSync(`${destination}/controlled-example-repairs.json`, JSON.stringify(report, null, 2));
console.log(JSON.stringify({ repairedControls: report.length, report }, null, 2));
