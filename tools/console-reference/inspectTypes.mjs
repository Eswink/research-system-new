import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const parsed = ts.getParsedCommandLineOfConfigFile(
  path.resolve("apps/web/tsconfig.json"),
  { noEmit: true },
  {
    ...ts.sys,
    onUnRecoverableConfigFileDiagnostic: (d) => {
      throw new Error(ts.flattenDiagnosticMessageText(d.messageText, " "));
    },
  },
);
const program = ts.createProgram(parsed.fileNames, parsed.options);
const items = ts.getPreEmitDiagnostics(program).map((d) => {
  const pos =
    d.file && d.start !== undefined ? d.file.getLineAndCharacterOfPosition(d.start) : null;
  return {
    file: d.file?.fileName,
    line: pos ? pos.line + 1 : 0,
    start: d.start,
    length: d.length,
    code: d.code,
    message: ts.flattenDiagnosticMessageText(d.messageText, " "),
  };
});
fs.mkdirSync("scratch/console-reference", { recursive: true });
fs.writeFileSync("scratch/console-reference/type-diagnostics.json", JSON.stringify(items, null, 2));
const counts = {};
for (const x of items) counts[x.code] = (counts[x.code] ?? 0) + 1;
console.log("diagnostics", items.length, counts);
console.log(JSON.stringify(items.slice(0, 30), null, 2));
