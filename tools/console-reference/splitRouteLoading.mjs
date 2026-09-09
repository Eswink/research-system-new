import fs from "node:fs";

// Static, literal imports remain discoverable to Vite. No runtime path construction or CDN.
function split(file, prefix) {
  let source = fs.readFileSync(file, "utf8");
  const declarations = [];
  source = source.replace(
    /^import \{ ([A-Z][A-Za-z0-9]+) \} from "([^"]+)";\r?\n/gm,
    (original, name, specifier) => {
      if (!specifier.startsWith(prefix)) return original;
      declarations.push(
        `const ${name} = lazy(() => import("${specifier}")\n` +
          `  .then((loaded) => ({ default: loaded.${name} })));`,
      );
      return "";
    },
  );
  if (declarations.length === 0) throw new Error(`No eager page imports found in ${file}`);
  const imports = [...source.matchAll(/^import[^;]+;\r?\n/gm)];
  const last = imports.at(-1);
  if (!last) throw new Error(`No import block in ${file}`);
  const offset = last.index + last[0].length;
  source = source.slice(0, offset) + "\n" + declarations.join("\n") + "\n" + source.slice(offset);
  source = source.replace(
    'import type { ReactNode } from "react";',
    'import { lazy, Suspense, type ReactNode } from "react";',
  );
  fs.writeFileSync(file, source, "utf8");
  console.log(file, "route chunks", declarations.length);
}

split("apps/web/src/features/example-console/ExamplePage.tsx", "./");
split("apps/web/src/navigation/PageRenderer.tsx", "../features/");
