import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const cli = path.join(root, "node_modules", "dependency-cruiser", "bin", "dependency-cruise.mjs");
const config = path.join(root, "dependency-cruiser.config.mjs");

const cruise = (fixture) =>
  spawnSync(process.execPath, [cli, "--config", config, "--output-type", "json", fixture], {
    cwd: root,
    encoding: "utf8",
    env: { ...process.env, FORCE_COLOR: "0" },
  });

test("允许的依赖图通过全部架构边界", () => {
  const result = cruise("tests/architecture/typescript/fixtures/valid");
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  assert.deepEqual(report.summary.violations, []);
});

test("负向依赖图命中每一类架构规则", () => {
  const result = cruise("tests/architecture/typescript/fixtures/invalid");
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  assert.ok(report.summary.error >= 8, "负向夹具必须产生架构错误");
  const observedRules = new Set(report.summary.violations.map(({ rule }) => rule.name));
  const expectedRules = new Set([
    "no-circular",
    "not-to-unresolvable",
    "domain-not-to-outer-layers",
    "domain-not-to-provider-or-runtime",
    "application-not-to-outer-layers",
    "entry-not-to-domain",
    "adapter-not-to-entry",
    "production-not-to-test-support",
  ]);
  assert.deepEqual(observedRules, expectedRules);
});
