import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const sourceRoot = path.resolve(fileURLToPath(new URL("../../src/", import.meta.url))) + path.sep;

export async function load(url, context, nextLoad) {
  if (!url.startsWith("file:") || !url.endsWith(".css")) return nextLoad(url, context);
  const file = fileURLToPath(url);
  if (!path.resolve(file).startsWith(sourceRoot)) return nextLoad(url, context);
  const source = await readFile(file, "utf8");
  const classes = Object.fromEntries([...source.matchAll(/\.([A-Za-z_][A-Za-z0-9_-]*)/g)]
    .map((match) => [match[1], match[1]]));
  return { format: "module", shortCircuit: true, source: `export default ${JSON.stringify(classes)};` };
}
