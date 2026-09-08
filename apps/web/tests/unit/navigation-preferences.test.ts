/**
 * 导航与布局逻辑单元测试（node:test，PLAN-20260908-033 STEP-03）：
 * - hash 路由解析：合法域/页、未知回退、setup 直达；
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
  DOMAIN_PAGES,
  SETUP_ROUTE,
  hashToRoute,
  routeToHash,
  type Route,
} from "../../src/navigation/routes";

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
  assert.deepEqual(hashToRoute("#/govern/operations"), {
    domain: "govern",
    page: "operations",
  });
  assert.deepEqual(hashToRoute("#/setup"), SETUP_ROUTE);
});

test("hashToRoute: 未知路由回退 plan/protocol", () => {
  assert.deepEqual(hashToRoute(""), { domain: "plan", page: "protocol" });
  assert.deepEqual(hashToRoute("#/bogus/page"), { domain: "plan", page: "protocol" });
  assert.deepEqual(hashToRoute("#/plan/unknown"), { domain: "plan", page: "protocol" });
});

test("hashToRoute: 域内缺页回退默认页", () => {
  assert.deepEqual(hashToRoute("#/assets"), { domain: "assets", page: "endpoints" });
  assert.deepEqual(hashToRoute("#/govern/"), { domain: "govern", page: "approvals" });
});

test("routeToHash 与 hashToRoute 往返一致", () => {
  for (const domain of Object.keys(DOMAIN_PAGES) as (keyof typeof DOMAIN_PAGES)[]) {
    for (const page of DOMAIN_PAGES[domain]) {
      const route: Route = { domain, page };
      assert.deepEqual(hashToRoute(routeToHash(route)), route);
    }
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
