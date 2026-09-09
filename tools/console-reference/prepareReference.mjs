import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import * as prettier from "prettier";
const target = "apps/web/src/features/example-console/command-center";
for (const script of ["refineTypes", "extractStyles"]) {
  const result = spawnSync(process.execPath, [`tools/console-reference/${script}.mjs`, target], {
    encoding: "utf8",
    stdio: "pipe",
  });
  console.log(result.stdout);
  if (result.status) throw new Error(result.stderr);
}
for (const entry of fs.readdirSync(target)) {
  const file = path.join(target, entry);
  if (!/\.(tsx?|css)$/.test(file)) continue;
  const options = await prettier.resolveConfig(file);
  const formatted = await prettier.format(fs.readFileSync(file, "utf8"), {
    ...options,
    filepath: file,
  });
  fs.writeFileSync(file, formatted, "utf8");
}
console.log("Native mission-control source formatted");
