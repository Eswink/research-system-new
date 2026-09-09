/** Move compiler-extracted presentation sections into their owning page modules. */
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
const program = ts.createProgram(cfg.fileNames, cfg.options),
  checker = program.getTypeChecker();
const roots = [
  "apps/web/src/features/example-console/reference",
  "apps/web/src/features/example-console/command-center",
];
const candidates = roots.flatMap((root) =>
  fs
    .readdirSync(root)
    .filter((f) => f.endsWith(".tsx"))
    .map((f) => path.resolve(root, f)),
);
const kebab = (s) =>
  s
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/([A-Z])([A-Z][a-z])/g, "$1-$2")
    .toLowerCase();
const exported = (n) => n.modifiers?.some((m) => m.kind === ts.SyntaxKind.ExportKeyword) === true;
const topNames = (n) =>
  ts.isVariableStatement(n)
    ? n.declarationList.declarations.filter((d) => ts.isIdentifier(d.name)).map((d) => d.name)
    : n.name
      ? [n.name]
      : [];
const isType = (n) => ts.isInterfaceDeclaration(n) || ts.isTypeAliasDeclaration(n);
const plan = [];
for (const file of candidates) {
  const sf = program.getSourceFile(file);
  if (!sf) continue;
  const decls = sf.statements.filter(
    (n) =>
      (ts.isFunctionDeclaration(n) || ts.isVariableStatement(n) || isType(n)) && topNames(n).length,
  );
  const helpers = decls.filter((n) => ts.isFunctionDeclaration(n) && !exported(n));
  if (!helpers.length || sf.text.split("\n").length < 210) continue;
  const symbols = new Map(),
    owners = new Map(),
    groups = new Map();
  for (const d of decls)
    for (const id of topNames(d)) {
      const sym = checker.getSymbolAtLocation(id);
      if (sym) symbols.set(sym, d);
      owners.set(d, "main");
    }
  for (const fn of helpers) {
    const name = fn.name.text;
    owners.set(fn, name);
    const props = decls.find((n) => n.name?.text === name + "Props");
    if (props) owners.set(props, name);
  }
  for (const d of decls)
    if (owners.get(d) === "main" && !exported(d) && ts.isVariableStatement(d)) {
      // Immutable module constants shared by several sections become named page-local assets.
      const name = topNames(d)[0].text;
      owners.set(d, name);
    }
  const deps = new Map(decls.map((d) => [d, new Set()]));
  for (const d of decls) {
    function scan(n) {
      if (ts.isIdentifier(n)) {
        const target = symbols.get(checker.getSymbolAtLocation(n));
        if (target && target !== d) deps.get(d).add(target);
      }
      ts.forEachChild(n, scan);
    }
    scan(d);
  }
  // A helper depending on an exported owner, or on another helper retained with it, stays local.
  let changed = true;
  while (changed) {
    changed = false;
    for (const d of decls) {
      const owner = owners.get(d);
      if (owner === "main") continue;
      if ([...deps.get(d)].some((x) => owners.get(x) === "main" && !isType(x))) {
        for (const [decl, o] of owners) if (o === owner) owners.set(decl, "main");
        changed = true;
      }
    }
  }
  // Move shared local type-only declarations into a bounded local types module.
  for (const d of decls)
    if (owners.get(d) === "main" && isType(d) && !exported(d)) {
      const usedByMoved = decls.some(
        (other) => owners.get(other) !== "main" && deps.get(other).has(d),
      );
      if (usedByMoved) owners.set(d, "pageTypes");
    }
  for (const [d, owner] of owners) {
    if (!groups.has(owner)) groups.set(owner, []);
    groups.get(owner).push(d);
  }
  if (groups.size === 1) continue;
  // Refuse circular module splits instead of generating runtime cycles.
  const graph = new Map([...groups.keys()].map((k) => [k, new Set()]));
  for (const d of decls)
    for (const dep of deps.get(d)) {
      const a = owners.get(d),
        b = owners.get(dep);
      if (a !== b && !isType(dep)) graph.get(a).add(b);
    }
  function cycle(id, visiting = new Set(), visited = new Set()) {
    if (visiting.has(id)) return true;
    if (visited.has(id)) return false;
    visiting.add(id);
    for (const next of graph.get(id) ?? []) if (cycle(next, visiting, visited)) return true;
    visiting.delete(id);
    visited.add(id);
    return false;
  }
  if ([...graph.keys()].some((id) => cycle(id))) {
    console.log("Retained cyclic local group", path.basename(file));
    continue;
  }
  const folder = path.join(path.dirname(file), kebab(path.basename(file, ".tsx")));
  const destinations = new Map(
    [...groups.keys()].map((k) => [k, k === "main" ? file : path.join(folder, k + ".tsx")]),
  );
  const originalImports = sf.statements.filter(ts.isImportDeclaration);
  const special = sf.statements.filter((n) => !decls.includes(n) && !ts.isImportDeclaration(n));
  for (const [owner, stmts] of groups) {
    const target = destinations.get(owner),
      imports = [];
    for (const imp of originalImports) {
      let content = imp.getText(sf);
      const spec = imp.moduleSpecifier.text;
      if (spec.startsWith(".")) {
        let rel = path
          .relative(path.dirname(target), path.resolve(path.dirname(file), spec))
          .replaceAll("\\", "/");
        if (!rel.startsWith(".")) rel = "./" + rel;
        content = content.replace(JSON.stringify(spec), JSON.stringify(rel));
      }
      imports.push(content);
    }
    const external = new Map();
    for (const stmt of stmts)
      for (const dep of deps.get(stmt)) {
        const other = owners.get(dep);
        if (other === owner) continue;
        let rel = path
          .relative(path.dirname(target), destinations.get(other))
          .replaceAll("\\", "/")
          .replace(/\.tsx$/, "");
        if (!rel.startsWith(".")) rel = "./" + rel;
        const key = (isType(dep) ? "type " : "") + rel;
        if (!external.has(key)) external.set(key, new Set());
        for (const name of topNames(dep)) external.get(key).add(name.text);
      }
    for (const [key, names] of external) {
      const type = key.startsWith("type "),
        spec = type ? key.slice(5) : key;
      imports.push(
        `import ${type ? "type " : ""}{ ${[...names].join(", ")} } from ${JSON.stringify(spec)};`,
      );
    }
    const body = stmts
      .map((stmt) => {
        const neededOutside = decls.some(
          (other) => owners.get(other) !== owner && deps.get(other).has(stmt),
        );
        return (neededOutside && !exported(stmt) ? "export " : "") + stmt.getText(sf);
      })
      .join("\n\n");
    const remaining = owner === "main" ? special.map((n) => n.getText(sf)).join("\n") : "";
    let content = imports.join("\n") + "\n\n" + body + "\n" + remaining + "\n";
    content = await prettier.format(content, {
      ...(await prettier.resolveConfig(file)),
      filepath: target,
    });
    const parsed = ts.createSourceFile(
      target,
      content,
      ts.ScriptTarget.Latest,
      true,
      ts.ScriptKind.TSX,
    );
    if (parsed.parseDiagnostics.length) throw new Error("Refused invalid moved module " + target);
    plan.push({ target, content, source: file });
  }
  console.log(path.basename(file), "->", groups.size, "owned modules");
}
for (const { target, content, source } of plan) {
  const backup =
    "scratch/console-reference/before-modularization/" +
    path.relative(process.cwd(), source).replaceAll("\\", "/");
  if (!fs.existsSync(backup)) {
    fs.mkdirSync(path.dirname(backup), { recursive: true });
    fs.writeFileSync(backup, fs.readFileSync(source));
  }
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, content, "utf8");
}
fs.writeFileSync(
  "scratch/console-reference/module-moves.json",
  JSON.stringify(
    plan.map(({ target, source }) => ({ target, source })),
    null,
    2,
  ),
);
console.log("Wrote", plan.length, "modules; imports will be organized by the compiler next");
