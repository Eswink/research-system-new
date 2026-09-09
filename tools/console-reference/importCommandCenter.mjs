/** Import the independent mission-control board as native, example-only React modules. */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const source = "docs/references/design/console-design/Command Center.html";
const html = fs.readFileSync(source, "utf8");
const script = html.match(/<script type="text\/babel">([\s\S]*?)<\/script>/)[1];
const sf = ts.createSourceFile(source, script, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const declarations = new Map();
for (const stmt of sf.statements) {
  if (!ts.isVariableStatement(stmt)) continue;
  for (const d of stmt.declarationList.declarations)
    if (ts.isIdentifier(d.name) && !["applyScale", "root"].includes(d.name.text))
      declarations.set(d.name.text, d);
}
const root = "apps/web/src/features/example-console/command-center";
fs.mkdirSync(root, { recursive: true });
const known = new Set(
  fs
    .readdirSync("apps/web/src/features/example-console/reference")
    .filter((n) => n.endsWith(".tsx"))
    .map((n) => n.slice(0, -4)),
);
const fixtures = {
  FIX_PROJECTS: "projects",
  FIX_AGENTS: "agents",
  FIX_ALERT_INBOX: "alert-inbox",
  FIX_RUNS_HISTORY: "runs-history",
  FIX_CLAIMS: "claims",
  FIX_EVIDENCE: "evidence",
  FIX_EVENTS: "events",
  FIX_MODELS: "models",
  FIX_ENDPOINTS: "endpoints",
  FIX_EXPERIMENT_QUEUE: "experiment-queue",
  FIX_EXPERIMENTS: "experiments",
  FIX_BUDGET: "budget",
  FIX_COST_DAILY: "cost-daily",
  FIX_COST_SANKEY: "cost-sankey",
  FIX_RUN: "run",
  FIX_APPROVALS: "approvals",
};
const annotations = {
  Panel:
    "{ kicker: string; title: string; right?: R.ReactNode; children: R.ReactNode; style?: R.CSSProperties }",
  StatBlock: "{ label: string; value: R.ReactNode; sub?: string; color?: string }",
};
for (const [name, d] of declarations) {
  let body = d.initializer.getText(sf);
  if (annotations[name]) {
    const param = d.initializer.parameters[0];
    const end = param.name.end - d.initializer.getStart(sf);
    body = body.slice(0, end) + ": " + annotations[name] + body.slice(end);
  }
  if (name === "CommandCenter")
    body = body.replace(
      /const \[clock, setClock\] = useState\(new Date\(\)\);[\s\S]*?\}, \[\]\);/,
      'const clock = new Date("2026-08-27T14:42:11Z");',
    );
  body = body.replace("ALL SYSTEMS · NOMINAL", "EXAMPLE · NOT LIVE");
  const ids = new Set();
  function walk(n) {
    if (ts.isIdentifier(n)) ids.add(n.text);
    ts.forEachChild(n, walk);
  }
  walk(d.initializer);
  const imports = [];
  if (annotations[name]) imports.push('import type * as R from "react";');
  if (ids.has("React")) imports.push('import * as React from "react";');
  const hooks = ["useState", "useEffect", "useMemo"].filter(
    (k) => ids.has(k) && name !== "CommandCenter",
  );
  if (hooks.length) imports.push(`import { ${hooks.join(", ")} } from "react";`);
  for (const dep of ids) {
    if (declarations.has(dep) && dep !== name) imports.push(`import { ${dep} } from "./${dep}";`);
    else if (known.has(dep)) imports.push(`import { ${dep} } from "../reference/${dep}";`);
    else if (Object.hasOwn(fixtures, dep))
      imports.push(`import ${dep} from "../data/${fixtures[dep]}.json";`);
  }
  const text =
    imports.join("\n") +
    `\n\n/** Reference: Command Center.html; every metric is a fixed example. */\nexport const ${name} = ${body};\n`;
  fs.writeFileSync(path.join(root, name + ".tsx"), text, "utf8");
}
const style = html.match(/<style>([\s\S]*?)<\/style>/)[1];
fs.writeFileSync(
  path.join(root, "command-center.css"),
  style.replace(/html, body \{[^}]*\}/, "") + "\n",
  "utf8",
);
console.log("Imported command-center modules:", [...declarations.keys()].join(", "));
