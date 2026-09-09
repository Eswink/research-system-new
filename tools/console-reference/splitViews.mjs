/** Compiler-assisted extraction of pure visual subtrees; does not suppress any quality gate. */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import * as prettier from "prettier";
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
const host = {
  ...ts.sys,
  useCaseSensitiveFileNames: () => ts.sys.useCaseSensitiveFileNames,
  getCompilationSettings: () => cfg.options,
  getScriptFileNames: () => cfg.fileNames,
  getScriptVersion: (f) => {
    try {
      return String(fs.statSync(f).mtimeMs);
    } catch {
      return "0";
    }
  },
  getScriptSnapshot: (f) =>
    fs.existsSync(f) ? ts.ScriptSnapshot.fromString(fs.readFileSync(f, "utf8")) : undefined,
  getCurrentDirectory: () => process.cwd(),
  getDefaultLibFileName: ts.getDefaultLibFilePath,
};
const service = ts.createLanguageService(host);
const max = Number(process.argv[3] ?? 400);
const selected = process.argv[2];
const files = cfg.fileNames
  .filter(
    (file) =>
      file.replaceAll("\\", "/").includes("/apps/web/src/") &&
      file.endsWith(".tsx") &&
      !file.includes(".mimosa"),
  )
  .map((file) => path.resolve(file))
  .filter((file) => !selected || selected === "--all" || path.basename(file) === selected);
const blocked = new Set();
let extracts = 0;
const log = [];
function lines(text) {
  return text.split(/\r?\n/).filter((l) => l.trim() && !/^\s*(\/\/|\{\/\*)/.test(l)).length;
}
function isFunction(n) {
  return (
    (ts.isArrowFunction(n) || ts.isFunctionDeclaration(n) || ts.isFunctionExpression(n)) && n.body
  );
}
function candidate(sf) {
  const functions = [];
  function scan(n) {
    if (isFunction(n) && lines(n.getText(sf)) > 48) functions.push(n);
    ts.forEachChild(n, scan);
  }
  scan(sf);
  for (const fn of functions.sort((a, b) => b.end - b.pos - (a.end - a.pos))) {
    const nodes = [];
    function visit(n) {
      if (ts.isJsxElement(n) || ts.isJsxFragment(n) || ts.isJsxSelfClosingElement(n)) {
        const text = n.getText(sf),
          size = lines(text),
          key = sf.fileName + ":" + text;
        if (size >= 12 && size <= 60 && !blocked.has(key)) nodes.push({ n, size, key });
      }
      ts.forEachChild(n, visit);
    }
    visit(fn.body);
    nodes.sort((a, b) => b.size - a.size);
    if (nodes.length) return nodes[0];
  }
  return undefined;
}
const camel = (s) =>
  s
    .split(/[^a-zA-Z0-9]+/)
    .filter(Boolean)
    .map((x) => x[0].toUpperCase() + x.slice(1))
    .join("");
function componentName(sf, node) {
  const stem = path.basename(sf.fileName, ".tsx").replace(/Screen$/, "");
  const text = node.getText(sf);
  const tag = ts.isJsxElement(node)
    ? node.openingElement.tagName.getText(sf)
    : ts.isJsxSelfClosingElement(node)
      ? node.tagName.getText(sf)
      : "Content";
  const key = text.match(/(?:title|label)=\{t\("([\w.]+)"/);
  const part = key
    ? camel(key[1].split(".").slice(1).join("-"))
    : ({
        PageToolbar: "Toolbar",
        Drawer: "DetailsDrawer",
        Modal: "Dialog",
        svg: "Chart",
        div: "Section",
        span: "Label",
        button: "Action",
        Field: "Field",
        Panel: "Panel",
      }[tag] ?? tag);
  const classRole = text.match(/className=\{(?:visual|styles)\.([A-Za-z]+)\}/)?.[1];
  const semanticPart = !key && part === "Section" && classRole ? camel(classRole) : part;
  const prefix = stem + semanticPart;
  let name = prefix,
    seq = 2;
  while (
    sf.text.includes("function " + name + "(") ||
    sf.text.includes("interface " + name + "Props")
  )
    name = prefix + seq++;
  return name;
}
async function apply(file, c) {
  const sf = service.getProgram().getSourceFile(file);
  const range = { pos: c.n.getStart(sf), end: c.n.end };
  const options = { indentSize: 2, tabSize: 2, newLineCharacter: "\n", convertTabsToSpaces: true };
  const ref = service
    .getApplicableRefactors(file, range, options)
    .find((r) => r.name === "Extract Symbol" && r.description === "Extract function");
  const action = ref?.actions.filter((a) => a.name.startsWith("function_scope")).at(-1);
  if (!action) {
    blocked.add(c.key);
    return false;
  }
  const result = service.getEditsForRefactor(file, options, range, ref.name, action.name, {});
  if (!result || result.edits.length !== 1) {
    blocked.add(c.key);
    return false;
  }
  const changes = result.edits[0].textChanges;
  let output = sf.text;
  for (const change of [...changes].sort((a, b) => b.span.start - a.span.start))
    output =
      output.slice(0, change.span.start) +
      change.newText +
      output.slice(change.span.start + change.span.length);
  const fresh = ts.createSourceFile(file, output, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const generated = fresh.statements.find(
    (n) => ts.isFunctionDeclaration(n) && n.name?.text.startsWith("newFunction"),
  );
  if (!generated || !generated.name?.text.startsWith("newFunction")) {
    blocked.add(c.key);
    return false;
  }
  let unsafe = false;
  function inspect(n) {
    if (n.kind === ts.SyntaxKind.AnyKeyword || ts.isImportTypeNode(n)) unsafe = true;
    ts.forEachChild(n, inspect);
  }
  inspect(generated);
  if (
    unsafe ||
    generated.typeParameters?.length ||
    generated.parameters.some((p) => !ts.isIdentifier(p.name) || !p.type)
  ) {
    blocked.add(c.key);
    return false;
  }
  const name = componentName(sf, c.n),
    old = generated.name.text;
  const params = generated.parameters.map((p) => ({
    name: p.name.text,
    type: p.type.getText(fresh),
  }));
  if (
    params.length > 10 ||
    params.some((p) => p.type.length > 1500 || p.name === "key" || p.name === "ref")
  ) {
    blocked.add(c.key);
    return false;
  }
  const edits = [];
  function renameCalls(n) {
    if (ts.isCallExpression(n) && ts.isIdentifier(n.expression) && n.expression.text === old) {
      const args = params.map((p, i) => {
        const value = n.arguments[i]?.getText(fresh) ?? "undefined";
        return value === p.name ? p.name : `${p.name}: ${value}`;
      });
      const target =
        ts.isJsxExpression(n.parent) && !ts.isJsxAttribute(n.parent.parent) ? n.parent : n;
      edits.push({
        start: target.getStart(fresh),
        end: target.end,
        text: `<${name} {...{ ${args.join(", ")} }} />`,
      });
    }
    ts.forEachChild(n, renameCalls);
  }
  renameCalls(fresh);
  const properties = params.map((p) => `  ${p.name}: ${p.type};`).join("\n");
  const annotation = params.length
    ? `{ ${params.map((p) => p.name).join(", ")} }: ${name}Props`
    : "";
  const definition =
    (params.length ? `interface ${name}Props {\n${properties}\n}\n\n` : "") +
    `function ${name}(${annotation}) ${generated.body.getText(fresh)}`;
  edits.push({ start: generated.getStart(fresh), end: generated.end, text: definition });
  for (const e of edits.sort((a, b) => b.start - a.start))
    output = output.slice(0, e.start) + e.text + output.slice(e.end);
  const format = await prettier.resolveConfig(file);
  output = await prettier.format(output, { ...format, filepath: file });
  const checked = ts.createSourceFile(
    file,
    output,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TSX,
  );
  const excess = (source) => {
    let total = 0;
    const walk = (n) => {
      if (isFunction(n)) total += Math.max(0, lines(n.getText(source)) - 48);
      ts.forEachChild(n, walk);
    };
    walk(source);
    return total;
  };
  if (excess(checked) >= excess(sf)) {
    blocked.add(c.key);
    return false;
  }
  const names = checked.statements.filter(ts.isFunctionDeclaration).map((n) => n.name?.text);
  if (new Set(names).size !== names.length || checked.parseDiagnostics.length)
    throw new Error("Invalid extraction in " + file);
  const backup =
    "scratch/console-reference/before-extraction/" +
    path.relative(process.cwd(), file).replaceAll("\\", "/");
  if (!fs.existsSync(backup)) {
    fs.mkdirSync(path.dirname(backup), { recursive: true });
    fs.writeFileSync(backup, sf.text, "utf8");
  }
  blocked.add(c.key);
  fs.writeFileSync(file, output, "utf8");
  log.push({
    file: path.basename(file),
    component: name,
    props: params.map((p) => p.name),
    lines: c.size,
  });
  console.log(path.basename(file), name, params.length, "props");
  return true;
}
for (const file of files) {
  if (["Icon.tsx", "PECustomIcon.tsx"].includes(path.basename(file))) continue;
  let attempts = 0;
  while (extracts < max && attempts++ < 75) {
    const sf = service.getProgram().getSourceFile(file);
    const c = candidate(sf);
    if (!c) break;
    if (await apply(file, c)) extracts++;
  }
  if (extracts >= max) break;
}
fs.writeFileSync(
  "scratch/console-reference/component-extractions.json",
  JSON.stringify(log, null, 2),
);
console.log(
  "Extracted",
  extracts,
  "pure presentation components; unresolvable refactors skipped:",
  blocked.size,
);
