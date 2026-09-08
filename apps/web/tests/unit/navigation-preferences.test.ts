/**
 * 导航与布局逻辑单元测试（node:test，PLAN-20260908-034 T06/T07）：
 * - 规范路由解析：合法域/页直达、旧别名映射、未知进入 null（未找到页）；
 * - 路由往返（routeToHash ↔ hashToRoute）；
 * - 偏好持久化：默认值、存取往返、非法值回退。
 */

import assert from "node:assert/strict";
import { afterEach, test } from "node:test";

import {
  applyPreferences,
  defaultPreferences,
  loadPreferences,
  savePreferences,
} from "../../src/layout/preferences";
import {
  CANONICAL_ROUTES,
  LEGACY_ALIASES,
  hashToRoute,
  routeToHash,
} from "../../src/navigation/registry";

// node:test 无 vite define；提供与生产一致的构建期常量替身
(globalThis as unknown as { __APP_VERSION__: string }).__APP_VERSION__ = "0.0.0-test";

afterEach(() => {
  delete (globalThis as { localStorage?: unknown }).localStorage;
  delete (globalThis as { document?: unknown }).document;
});

function installLocalStorage(initial: Record<string, string> = {}): void {
  const store = new Map<string, string>(Object.entries(initial));
  (globalThis as { window: unknown }).window = {
    localStorage: {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
      clear: () => {
        store.clear();
      },
      key: () => null,
      get length() {
        return store.size;
      },
    } as Storage,
  };
}

function installDocument(): void {
  const attributes: Record<string, string> = {};
  (globalThis as { document: Document }).document = {
    documentElement: {
      get lang() {
        return attributes.lang ?? "";
      },
      set lang(value: string) {
        attributes.lang = value;
      },
      dataset: {} as DOMStringMap,
    },
  } as unknown as Document;
}

test("hashToRoute: 合法域与页面解析", () => {
  assert.deepEqual(hashToRoute("#/plan/protocol"), { domain: "plan", page: "protocol" });
  assert.deepEqual(hashToRoute("#/govern/audit"), { domain: "govern", page: "audit" });
  assert.deepEqual(hashToRoute("#/settings/settings"), {
    domain: "settings",
    page: "settings",
  });
});

test("hashToRoute: 未知路由返回 null（进入未找到页）", () => {
  assert.equal(hashToRoute("#/bogus/page"), null);
  assert.equal(hashToRoute("#/plan/unknown"), null);
});

test("hashToRoute: 旧别名映射到规范路由", () => {
  assert.deepEqual(hashToRoute("#/assets/compute"), { domain: "ops", page: "compute" });
  assert.deepEqual(hashToRoute("#/govern/approvals"), { domain: "run", page: "approvals" });
  assert.deepEqual(hashToRoute("#/evidence/inspection"), { domain: "evidence", page: "claims" });
});

test("routeToHash 与 hashToRoute 往返一致（全部规范路由）", () => {
  assert.equal(CANONICAL_ROUTES.length, 33);
  for (const route of CANONICAL_ROUTES) {
    assert.deepEqual(hashToRoute(routeToHash(route)), route);
  }
});

test("LEGACY_ALIASES 全部映射到规范路由", () => {
  const canonical = new Set(CANONICAL_ROUTES.map((r) => `${r.domain}/${r.page}`));
  for (const alias of Object.values(LEGACY_ALIASES)) {
    const key = `${alias.domain}/${alias.page}`;
    assert.ok(canonical.has(key), `alias → ${key}`);
  }
});

test("preferences: 默认值 dark/normal/zh/form", () => {
  installLocalStorage();
  installDocument();
  const prefs = loadPreferences();
  assert.equal(prefs.theme, "dark");
  assert.equal(prefs.density, "normal");
  assert.equal(prefs.language, "zh");
  assert.equal(prefs.editorMode, "form");
});

test("preferences: 存取往返", () => {
  installLocalStorage();
  installDocument();
  const next = { ...defaultPreferences(), theme: "light", density: "compact" } as const;
  savePreferences(next);
  const loaded = loadPreferences();
  assert.equal(loaded.theme, "light");
  assert.equal(loaded.density, "compact");
});

test("preferences: 非法存储内容回退默认", () => {
  installLocalStorage({ "ros.console.preferences": "{not json" });
  installDocument();
  const prefs = loadPreferences();
  assert.equal(prefs.theme, "dark");
  assert.equal(prefs.language, "zh");
});

test("preferences: applyPreferences 写 document root", () => {
  installLocalStorage();
  installDocument();
  const prefs = { ...defaultPreferences(), theme: "light", language: "en" } as const;
  applyPreferences(prefs);
  const root = document.documentElement;
  assert.equal(root.dataset.theme, "light");
  assert.equal(root.dataset.density, "normal");
  assert.equal(root.lang, "en");
});
