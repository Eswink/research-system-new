import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const parsed = ts.getParsedCommandLineOfConfigFile(
  path.resolve("apps/web/tsconfig.json"),
  { noEmit: true },
  { ...ts.sys, onUnRecoverableConfigFileDiagnostic: () => {} },
);
const host = {
  getScriptFileNames: () => parsed.fileNames,
  getScriptVersion: () => "0",
  getScriptSnapshot: (file) =>
    fs.existsSync(file)
      ? ts.ScriptSnapshot.fromString(
          file.endsWith("ActionBar.tsx")
            ? fs
                .readFileSync(file, "utf8")
                .replace(
                  "({ dirty, canApply, errorCount, warnCount, onDiscard, onApply }) => {",
                  "(props) => { const { dirty, canApply, errorCount, warnCount, onDiscard, onApply } = props;",
                )
            : fs.readFileSync(file, "utf8"),
        )
      : undefined,
  getCurrentDirectory: () => path.resolve("apps/web"),
  getCompilationSettings: () => parsed.options,
  getDefaultLibFileName: (options) => ts.getDefaultLibFilePath(options),
  fileExists: ts.sys.fileExists,
  readFile: ts.sys.readFile,
  readDirectory: ts.sys.readDirectory,
};
const service = ts.createLanguageService(host);
const file = path.resolve("apps/web/src/features/example-console/reference/ActionBar.tsx");
const diagnostics = service.getSemanticDiagnostics(file);
const diag = diagnostics.find((d) => d.code === 7006);
const fixes = service.getCodeFixesAtPosition(
  file,
  diag.start,
  diag.start + diag.length,
  [diag.code],
  { indentSize: 2, tabSize: 2, convertTabsToSpaces: true },
  {},
);
console.log(JSON.stringify(fixes, null, 2));
