/** One-time native source migration. Generated TSX remains subject to all product gates. */
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { createRequire } from "node:module";

const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const origin = "docs/references/design/console-design";
const dest = "apps/web/src/features/example-console/reference";
if (fs.existsSync(dest)) throw new Error("Refuse to overwrite a migrated source directory");
fs.mkdirSync(dest, { recursive: true });
const sources = [
  "components/atoms.jsx",
  "components/charts.jsx",
  "components/patterns.jsx",
  "components/AppShell.jsx",
  ...fs
    .readdirSync(`${origin}/screens`)
    .filter((name) => name.endsWith(".jsx"))
    .map((name) => `screens/${name}`),
];
const skip = new Set(["DOMAINS", "AppShell"]);
const entries = [];
const locals = new Map();
const globals = new Map();
const lowerCamel = (name) => name.toLowerCase().replace(/_([a-z])/g, (_, x) => x.toUpperCase());
for (const source of sources) {
  const sf = ts.createSourceFile(
    source,
    fs.readFileSync(`${origin}/${source}`, "utf8"),
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.JSX,
  );
  const local = new Map();
  for (const st of sf.statements) {
    const declarations = ts.isVariableStatement(st)
      ? st.declarationList.declarations
      : ts.isFunctionDeclaration(st)
        ? [st]
        : [];
    for (const node of declarations) {
      if (!node.name || !ts.isIdentifier(node.name)) continue;
      const name = node.name.text;
      if (skip.has(name)) continue;
      let file = /^[A-Z_0-9]+$/.test(name) ? lowerCamel(name) : name;
      if (name === "INPUT") file = source.includes("Setup") ? "setupInput" : "protocolInput";
      if (name === "MetricCard" && source.includes("Budget")) file = "BudgetMetricCard";
      if (name === "validate") file = "validateProtocol";
      if (name === "serialize") file = "serializeProtocol";
      const text = ts.isFunctionDeclaration(node) ? node.getText(sf) : `const ${node.getText(sf)};`;
      const entry = { name, file, source, text, node, sf };
      entries.push(entry);
      local.set(name, entry);
      if (!globals.has(name)) globals.set(name, entry);
    }
  }
  locals.set(source, local);
}
const hookNames = new Set(["useState", "useEffect", "useMemo", "useCallback", "useRef"]);
const dataDir = "apps/web/src/features/example-console/data";
const datasets = new Set(
  fs
    .readdirSync(dataDir)
    .filter((n) => n.endsWith(".json"))
    .map((n) => "FIX_" + n.slice(0, -5).toUpperCase().replaceAll("-", "_")),
);
for (const entry of entries) {
  const ids = new Set();
  const visit = (node) => {
    if (ts.isIdentifier(node)) ids.add(node.text);
    ts.forEachChild(node, visit);
  };
  visit(entry.node);
  const imports = [];
  const hooks = [...hookNames].filter((name) => ids.has(name));
  if (hooks.length) imports.push(`import { ${hooks.join(", ")} } from "react";`);
  if (ids.has("React")) imports.push('import * as React from "react";');
  if (ids.has("useI18n"))
    imports.push('import { useExampleI18n as useI18n } from "../useExampleI18n";');
  for (const id of [...ids].sort()) {
    if (datasets.has(id)) {
      const slug = id.slice(4).toLowerCase().replaceAll("_", "-");
      imports.push(`import ${id} from "../data/${slug}.json";`);
      continue;
    }
    const dependency = locals.get(entry.source).get(id) ?? globals.get(id);
    if (dependency && dependency !== entry) {
      imports.push(`import { ${id} } from "./${dependency.file}";`);
    }
  }
  const jsx = /<[A-Za-z>]/.test(entry.text);
  const content =
    imports.join("\n") +
    `\n\n/** Reference: ${entry.source}; EXAMPLE ONLY. */\n` +
    "export " +
    entry.text +
    "\n";
  fs.writeFileSync(`${dest}/${entry.file}.${jsx ? "tsx" : "ts"}`, content, "utf8");
}
const i18n = ts.createSourceFile(
  "i18n.jsx",
  fs.readFileSync(`${origin}/components/i18n.jsx`, "utf8"),
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.JSX,
);
const declaration = i18n.statements
  .filter(ts.isVariableStatement)
  .flatMap((st) => [...st.declarationList.declarations])
  .find((d) => d.name.getText(i18n) === "STRINGS");
const strings = vm.runInNewContext(
  `(${declaration.initializer.getText(i18n)})`,
  {},
  { timeout: 1000 },
);
fs.writeFileSync(`${dataDir}/translations.json`, JSON.stringify(strings, null, 2) + "\n", "utf8");
fs.writeFileSync(
  `${dest}/migration-manifest.json`,
  JSON.stringify(
    entries.map(({ name, file, source }) => ({ name, file, source })),
    null,
    2,
  ) + "\n",
  "utf8",
);
console.log(`Imported ${entries.length} native declarations; no browser Babel, CDN or iframe.`);
console.log("Translation locales:", Object.keys(strings));
