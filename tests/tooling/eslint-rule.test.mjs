import assert from "node:assert/strict";
import { test } from "node:test";

import { Linter } from "eslint";
import tseslint from "typescript-eslint";

import architecture from "../../tools/eslint-rules/architecture.mjs";

const verify = (code) => {
  const linter = new Linter({ configType: "flat" });
  return linter.verify(
    code,
    [
      {
        files: ["**/*.ts"],
        languageOptions: { parser: tseslint.parser },
        plugins: { architecture },
        rules: { "architecture/require-never-default": "error" },
      },
    ],
    { filename: "fixture.ts" },
  );
};

test("switch default 必须执行 never 穷尽检查", () => {
  const messages = verify(`
    type State = { kind: "idle" } | { kind: "running" };
    const describe = (state: State): string => {
      switch (state.kind) {
        case "idle": return "idle";
        case "running": return "running";
        default: return "unknown";
      }
    };
  `);
  assert.deepEqual(
    messages.map(({ ruleId }) => ruleId),
    ["architecture/require-never-default"],
  );
});

test("assertNever default 满足穷尽约束", () => {
  const messages = verify(`
    type State = { kind: "idle" } | { kind: "running" };
    const assertNever = (value: never): never => { throw new Error(String(value)); };
    const describe = (state: State): string => {
      switch (state.kind) {
        case "idle": return "idle";
        case "running": return "running";
        default: return assertNever(state);
      }
    };
  `);
  assert.deepEqual(messages, []);
});
