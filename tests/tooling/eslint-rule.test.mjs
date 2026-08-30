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

const verifyLineLimits = (code, severity) => {
  const linter = new Linter({ configType: "flat" });
  const options = { softMax: 5, hardMax: 10 };
  return linter.verify(
    code,
    [
      {
        files: ["**/*.ts"],
        languageOptions: { parser: tseslint.parser },
        plugins: { architecture },
        rules: {
          "architecture/max-lines-soft": [severity === "warn" ? "warn" : "off", options],
          "architecture/max-lines-hard": [severity === "error" ? "error" : "off", options],
        },
      },
    ],
    { filename: "fixture.ts" },
  );
};

const linesOf = (count) => "const a = 1;\n".repeat(count);

test("行数软阈值内不报告", () => {
  assert.deepEqual(verifyLineLimits(linesOf(5), "warn"), []);
  assert.deepEqual(verifyLineLimits(linesOf(5), "error"), []);
});

test("软/硬之间仅触发 warn 档", () => {
  const warnMessages = verifyLineLimits(linesOf(7), "warn");
  assert.equal(warnMessages.length, 1);
  assert.equal(warnMessages[0].ruleId, "architecture/max-lines-soft");
  assert.equal(warnMessages[0].severity, 1);
  assert.deepEqual(verifyLineLimits(linesOf(7), "error"), []);
});

test("超过硬上限仅触发 error 档", () => {
  const errorMessages = verifyLineLimits(linesOf(11), "error");
  assert.equal(errorMessages.length, 1);
  assert.equal(errorMessages[0].ruleId, "architecture/max-lines-hard");
  assert.equal(errorMessages[0].severity, 2);
  assert.deepEqual(verifyLineLimits(linesOf(11), "warn"), []);
});

test("软阈值规则支持 skipBlankLines", () => {
  const linter = new Linter({ configType: "flat" });
  const messages = linter.verify(
    `${linesOf(5)}\n\n\n`,
    [
      {
        files: ["**/*.ts"],
        languageOptions: { parser: tseslint.parser },
        plugins: { architecture },
        rules: {
          "architecture/max-lines-soft": [
            "warn",
            { softMax: 5, hardMax: 10, skipBlankLines: true },
          ],
        },
      },
    ],
    { filename: "fixture.ts" },
  );
  assert.deepEqual(messages, []);
});
