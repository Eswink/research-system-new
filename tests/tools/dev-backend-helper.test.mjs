import assert from "node:assert/strict";
import { test } from "node:test";

import {
  gatewayBind,
  mergeEnv,
  parseDsnEndpoint,
  parseDotEnv,
} from "../../tools/dev-backend/lib.mjs";

test("parseDotEnv: basic, quotes, comments, later wins", () => {
  const body = [
    "# comment",
    "",
    "KEY=value",
    'QUOTED="a b c"',
    "SINGLE='x'",
    "KEY=second",
    "EMPTY=",
    "invalid line without equals",
  ].join("\n");
  assert.deepEqual(parseDotEnv(body), {
    KEY: "second",
    QUOTED: "a b c",
    SINGLE: "x",
    EMPTY: "",
  });
});

test("parseDotEnv: CRLF and whitespace-trimmed values", () => {
  const body = "A=  spaced  \r\nB=1";
  assert.deepEqual(parseDotEnv(body), { A: "spaced", B: "1" });
});

test("parseDsnEndpoint: host, port, password with colon, no-credential rejection", () => {
  assert.deepEqual(parseDsnEndpoint("postgresql://user:pass@127.0.0.1:15432"), {
    host: "127.0.0.1",
    port: 15432,
  });
  assert.deepEqual(parseDsnEndpoint("postgresql://user:we:ird@localhost"), {
    host: "localhost",
    port: 5432,
  });
  assert.deepEqual(parseDsnEndpoint("postgres://u@host:5432"), {
    host: "host",
    port: 5432,
  });
  assert.equal(parseDsnEndpoint("postgresql://127.0.0.1:5432/db"), null);
  assert.equal(parseDsnEndpoint(""), null);
  assert.equal(parseDsnEndpoint(undefined), null);
});

test("gatewayBind: defaults and env overrides", () => {
  assert.deepEqual(gatewayBind({}), { host: "127.0.0.1", port: "8081" });
  assert.deepEqual(
    gatewayBind({
      RESEARCHOS_WORKER_GATEWAY_HOST: "0.0.0.0",
      RESEARCHOS_WORKER_GATEWAY_PORT: "9090",
    }),
    { host: "0.0.0.0", port: "9090" },
  );
  assert.deepEqual(gatewayBind({ RESEARCHOS_WORKER_GATEWAY_HOST: "127.0.0.1" }), {
    host: "127.0.0.1",
    port: "8081",
  });
});

test("mergeEnv: host wins, dotenv fills only undefined keys", () => {
  const host = { A: "host-a", B: "host-b", C: undefined };
  const dotenv = { A: "dotenv-a", B: "dotenv-b", D: "dotenv-d" };
  assert.deepEqual(mergeEnv(host, dotenv), {
    A: "host-a",
    B: "host-b",
    C: undefined,
    D: "dotenv-d",
  });
});
