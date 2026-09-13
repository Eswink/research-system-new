/** activeProject 上下文测试（WP-C）：默认值、持久化回退、无 DOM 环境安全。 */

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  getActiveProjectId,
  setActiveProjectId,
  subscribeActiveProject,
} from "../../src/api/activeProject";

type FakeWindow = {
  localStorage: { getItem(key: string): string | null; setItem(key: string, value: string): void };
  addEventListener: (type: string, listener: () => void) => void;
  removeEventListener: (type: string, listener: () => void) => void;
  dispatchEvent: (event: unknown) => boolean;
};

function withWindow(body: () => void, events: string[] = []): void {
  const data = new Map<string, string>();
  const fake: FakeWindow = {
    localStorage: {
      getItem: (key) => data.get(key) ?? null,
      setItem: (key, value) => {
        data.set(key, value);
      },
    },
    addEventListener: (type) => {
      events.push(type);
    },
    removeEventListener: () => undefined,
    dispatchEvent: () => true,
  };
  const hadWindow = "window" in globalThis;
  Object.defineProperty(globalThis, "window", { value: fake, configurable: true });  try {
    body();
  } finally {
    if (!hadWindow) {
      Reflect.deleteProperty(globalThis, "window");
    }
  }
}

test("default project id resolves to example-project when storage is absent", () => {
  assert.equal(getActiveProjectId(), "example-project");
});

test("set persists and get reads back; empty set must not clobber", () => {
  withWindow(() => {
    setActiveProjectId("proj-42");
    assert.equal(getActiveProjectId(), "proj-42");
    setActiveProjectId("");
    assert.equal(getActiveProjectId(), "proj-42");
  });
});

test("subscribe registers listeners and unsubscribe is safe (no DOM event bus in node)", () => {
  const events: string[] = [];
  withWindow(() => {
    const off = subscribeActiveProject(() => undefined);
    assert.deepEqual(events, ["ros:active-project", "storage"]);
    assert.doesNotThrow(() => {
      off();
    });
  }, events);
});
