import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const config = ts.getParsedCommandLineOfConfigFile(
  path.resolve("apps/web/tsconfig.json"),
  {},
  { ...ts.sys, onUnRecoverableConfigFileDiagnostic: failConfig },
);
if (!config) throw new Error("Missing web TypeScript configuration");

function failConfig(diagnostic) {
  throw new Error(ts.flattenDiagnosticMessageText(diagnostic.messageText, "\n"));
}

// Analyze a fixed source snapshot. Applying edits during analysis causes TS to rebuild
// the entire strict project for each of the hundreds of migrated reference modules.
const snapshots = new Map();
function snapshot(file) {
  if (!snapshots.has(file) && fs.existsSync(file)) {
    snapshots.set(file, ts.ScriptSnapshot.fromString(fs.readFileSync(file, "utf8")));
  }
  return snapshots.get(file);
}

const host = {
  ...ts.sys,
  useCaseSensitiveFileNames: () => ts.sys.useCaseSensitiveFileNames,
  getCompilationSettings: () => config.options,
  getScriptFileNames: () => config.fileNames,
  getScriptVersion: () => "0",
  getScriptSnapshot: snapshot,
  getCurrentDirectory: () => process.cwd(),
  getDefaultLibFileName: ts.getDefaultLibFilePath,
};
const service = ts.createLanguageService(host);
const updates = [];
const files = config.fileNames.filter(
  (file) => file.replaceAll("\\", "/").includes("/apps/web/src/") && /\.tsx?$/.test(file),
);
for (const [index, file] of files.entries()) {
  updates.push(
    ...service.organizeImports(
      { type: "file", fileName: file },
      {},
      { preferTypeOnlyAutoImports: true },
    ),
  );
  if (index % 50 === 0) console.log("Analyzed", index + 1, "/", files.length);
}

for (const change of updates) {
  let source = fs.readFileSync(change.fileName, "utf8");
  for (const edit of [...change.textChanges].sort((a, b) => b.span.start - a.span.start)) {
    source =
      source.slice(0, edit.span.start) +
      edit.newText +
      source.slice(edit.span.start + edit.span.length);
  }
  fs.writeFileSync(change.fileName, source, "utf8");
}
service.dispose();
console.log("Organized", updates.length, "native modules from one compiler snapshot");
