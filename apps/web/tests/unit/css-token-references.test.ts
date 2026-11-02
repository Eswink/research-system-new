/**
 * CSS 自定义属性引用必须**真的存在**（GOAL-20261103-104 EC-01 的机械判据）。
 *
 * **补的是哪一格**：CSS-module 的 TypeScript 类型是 `{ readonly [key: string]: string }`
 * ⇒ `styles.anything` 都能过 typecheck；`var(--anything)` 也能过。拼错的类名 / 未定义的
 * token **不会**让任何一道门变红，只会让样式静默失效。2026-11-03 实测到三处：
 *
 * - `PhaseProgress.tsx` 的 `PhaseDetail` 引 `styles.muted`，而 `LivePage.module.css` 里
 *   **没有** `.muted` ⇒ 两处渲染成 `className={undefined}`；
 * - `CommandCenterPage.module.css` / `ConsoleLoading.module.css` 用 `var(--bg)`，而
 *   `tokens.css` 里叫 `--bg-app`；
 * - `LivePage.module.css` 用 `var(--text-dim)`，最接近的是 `--fg-faint`。
 *
 * 判据两面：
 * 1. **token 面**：`src/**\/*.module.css` 里每个 `var(--x)` 的 `x` 必须要么在
 *    `src/styles/tokens.css` 定义，要么在**局部**模块里自己定义（`example-console` 的
 *    `--cc-*` 在 `CommandCenterStage.module.css` 的 `:root` 里定义，靠层叠传给子树）；
 * 2. **类名面**：`.tsx` 里 `styles.<key>` 的 `key` 必须在该文件 import 的那个
 *    `*.module.css` 里真的存在（这正是 `.muted` 那处静默失效的形状）。
 *
 * **局部白名单不是刷数字**：白名单按**模块文件名**限定（不是按 token 名），且要求该 token
 * 在**同一个模块**里被定义 —— 只把「谁定义了它」从全局单点放宽到「自己模块内部」，
 * 没有放宽「必须有人定义」。
 */

import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const SRC = path.join(path.dirname(fileURLToPath(import.meta.url)), "../../src");
const TOKENS = path.join(SRC, "styles", "tokens.css");

/**
 * **局部白名单不是刷数字**：白名单按**目录**限定（一个目录 = 一份 CSS 层叠），且要求该
 * token 在**同目录的某个模块**里真的被定义 —— 只把「谁定义了它」从全局单点放宽到
 * 「同一层叠内的兄弟模块」，**没有**放宽「必须有人定义」。
 *
 * 为什么需要它：`--cc-*` 定义在 `CommandCenterStage.module.css` 的 `.wrapper` 上
 * （不是 `:root`），靠 **DOM 嵌套**传给整棵 command-center 子树。静态判据看不见 DOM
 * 结构 ⇒ 「兄弟模块引它」在运行时成立、在文本上不可证。只对**这一族**登记。
 */
const LOCAL_CASCADE_DIRS = new Set(["features/example-console/command-center"]);

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) {
      walk(full, out);
    } else {
      out.push(full);
    }
  }
  return out;
}

const relative = (file: string): string => path.relative(SRC, file).split(path.sep).join("/");

/** 一个 CSS 文本里**定义**的自定义属性名（`--x: value`）。 */
function definedTokens(css: string): Set<string> {
  const defined = new Set<string>();
  for (const match of css.matchAll(/(--[A-Za-z0-9-]+)\s*:/g)) {
    defined.add(match[1] ?? "");
  }
  return defined;
}

/** 一个 CSS 文本里**引用**的自定义属性名（`var(--x)`，可带 fallback）。 */
function referencedTokens(css: string): Set<string> {
  const referenced = new Set<string>();
  for (const match of css.matchAll(/var\(\s*(--[A-Za-z0-9-]+)/g)) {
    referenced.add(match[1] ?? "");
  }
  return referenced;
}

test("every var(--token) in a CSS module resolves to a real definition", () => {
  const tokensCss = readFileSync(TOKENS, "utf8");
  const globalDefined = definedTokens(tokensCss);
  assert.ok(
    globalDefined.size > 40,
    `tokens.css only yielded ${String(globalDefined.size)} definitions; regex or file moved`,
  );

  const moduleFiles = walk(SRC).filter((file) => file.endsWith(".module.css"));
  assert.ok(moduleFiles.length > 20, `only ${String(moduleFiles.length)} CSS modules found`);
  const localDefined = new Map<string, Set<string>>();
  for (const file of moduleFiles) {
    localDefined.set(relative(file), definedTokens(readFileSync(file, "utf8")));
  }
  // 每个受准目录下**所有**兄弟模块定义的 token 并集（一份层叠）。
  const cascadeDefined = new Map<string, Set<string>>();
  for (const [rel, tokens] of localDefined) {
    const dir = path.posix.dirname(rel);
    if (!LOCAL_CASCADE_DIRS.has(dir)) {
      continue;
    }
    const bucket = cascadeDefined.get(dir) ?? new Set<string>();
    for (const token of tokens) {
      bucket.add(token);
    }
    cascadeDefined.set(dir, bucket);
  }

  const offenders: string[] = [];
  for (const file of moduleFiles) {
    const rel = relative(file);
    const cascade = cascadeDefined.get(path.posix.dirname(rel)) ?? new Set<string>();
    for (const token of referencedTokens(readFileSync(file, "utf8"))) {
      if (globalDefined.has(token) || cascade.has(token)) {
        continue;
      }
      offenders.push(`${rel}: var(${token}) is not defined in tokens.css nor locally`);
    }
  }
  assert.deepEqual(offenders, [], offenders.join("\n"));
});

test("every styles.<key> resolves to a class in the imported CSS module", () => {
  const byDirectory = new Map<string, Set<string>>();
  for (const file of walk(SRC)) {
    if (file.endsWith(".module.css")) {
      byDirectory.set(path.dirname(file), definedTokens(readFileSync(file, "utf8")));
    }
  }
  // 类名不是自定义属性 ⇒ 单独取 `.name`。
  const classNames = (css: string): Set<string> => {
    const names = new Set<string>();
    for (const match of css.matchAll(/\.([A-Za-z_][A-Za-z0-9_-]*)/g)) {
      names.add(match[1] ?? "");
    }
    return names;
  };

  const offenders: string[] = [];
  let checked = 0;
  for (const file of walk(SRC)) {
    if (!file.endsWith(".tsx") && !file.endsWith(".ts")) {
      continue;
    }
    const source = readFileSync(file, "utf8");
    for (const match of source.matchAll(
      /import\s+(\w+)\s+from\s+"([^"]+\.module\.css)"/g,
    )) {
      const alias = match[1] ?? "";
      const spec = match[2] ?? "";
      const cssPath = path.resolve(path.dirname(file), spec);
      const classes = classNames(readFileSync(cssPath, "utf8"));
      for (const use of source.matchAll(new RegExp(`\\b${alias}\\.([A-Za-z_$][\\w$]*)`, "g"))) {
        const key = use[1] ?? "";
        checked += 1;
        if (!classes.has(key)) {
          offenders.push(
            `${relative(file)}: ${alias}.${key} is not a class in ${relative(cssPath)}`,
          );
        }
      }
    }
  }
  assert.ok(
    checked > 100,
    `only ${String(checked)} styles.* usages scanned: the detector went blind`,
  );
  assert.deepEqual(offenders, [], offenders.join("\n"));
});

test("the detector actually bites: an injected var(--not-a-token) is reported", () => {
  // 反证臂：判据不是空断言。用**同一个**判定函数喂一段合成文本，必须点名变量名。
  const synthetic = ".x { color: var(--not-a-token); }";
  const tokensCss = readFileSync(TOKENS, "utf8");
  const globalDefined = definedTokens(tokensCss);
  const missing = [...referencedTokens(synthetic)].filter((token) => !globalDefined.has(token));
  assert.deepEqual(
    missing,
    ["--not-a-token"],
    "the reference extractor stopped seeing an undefined token",
  );
  // 并且类名面也咬得住：`.muted` 这个词确实不在 LivePage 模块里（这正是本轮修的缺陷）。
  const liveCss = readFileSync(
    path.join(SRC, "features/shared/LivePage.module.css"),
    "utf8",
  );
  assert.notEqual(
    liveCss.includes(".muted"),
    true,
    "LivePage.module.css grew a .muted: PhaseProgress must import the local module then",
  );
});
