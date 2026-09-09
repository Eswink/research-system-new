import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const cfg = ts.getParsedCommandLineOfConfigFile(
  path.resolve("apps/web/tsconfig.json"),
  {},
  { ...ts.sys, onUnRecoverableConfigFileDiagnostic: () => {} },
);
const host = {
  ...ts.sys,
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
const file = path.resolve("apps/web/src/features/example-console/reference/ProjectsScreen.tsx");
const sf = service.getProgram().getSourceFile(file);
let target;
function find(n) {
  if (ts.isJsxElement(n) && n.openingElement.tagName.getText(sf) === "PageToolbar") target = n;
  ts.forEachChild(n, find);
}
find(sf);
const range = { pos: target.getStart(sf), end: target.end };
const refs = service.getApplicableRefactors(file, range, {});
console.log(JSON.stringify(refs));
const ref = refs.find((r) => r.name === "Extract Symbol");
const action = ref?.actions.filter((a) => a.name.startsWith("function_scope")).at(-1);
if (action) {
  const edits = service.getEditsForRefactor(file, {}, range, ref.name, action.name, {});
  fs.writeFileSync("scratch/console-reference/refactor-probe.json", JSON.stringify(edits, null, 2));
  console.log(JSON.stringify(edits).slice(0, 8000));
}
