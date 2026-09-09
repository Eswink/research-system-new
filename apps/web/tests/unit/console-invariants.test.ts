import assert from "node:assert/strict";
import { test } from "node:test";
import { ledgerMinorText, ledgerQuantityText, ledgerSummary } from
  "../../src/features/budget/ledgerPresentation";
import { buildProvenance, layoutProvenance } from "../../src/features/lineage/provenanceModel";
import { taskProgress, usageSummary } from "../../src/features/overview/overviewPresentation";
import { parseRunEventFrame } from "../../src/features/runs/eventFrame";
import { editedModelBinding } from "../../src/features/team/modelBinding";
import { parseSourceSelection, resolveDataSource } from "../../src/navigation/presentationPolicy";
import { CANONICAL_ROUTES } from "../../src/navigation/registry";
import { parseContext, stripContext, withContext } from "../../src/navigation/urlContext";
import { claimsView, eventFrame, evidenceRecord, usageEntry, usageView } from "./consoleFixtures";

test("every route honors live/example selection with no request-dependent fallback", () => {
  for (const route of CANONICAL_ROUTES) {
    assert.equal(resolveDataSource(route, "live"), "live");
    assert.equal(resolveDataSource(route, "example"), "example");
  }
  assert.equal(resolveDataSource({ domain: "library", page: "prompts" }, "auto"), "example");
  assert.equal(resolveDataSource({ domain: "run", page: "timeline" }, "auto"), "live");
  assert.equal(parseSourceSelection("?source=untrusted"), "auto");
});

test("Run and Draft URL context round trips without admitting credential parameters", () => {
  const context = { runId: "run/# ?&", draftId: "draft?&/#" };
  const hash = withContext("#/plan/protocol", context);
  assert.deepEqual(parseContext(hash), context);
  assert.equal(stripContext(hash), "#/plan/protocol");
  assert.deepEqual(parseContext("#/run/timeline?api_key=canary&run=one"), {
    runId: "one", draftId: "",
  });
});

test("unknown costs and quantities never render as measured zero or known subtotal", () => {
  assert.equal(ledgerMinorText(null, "JPY"), "UNKNOWN (not 0)");
  assert.equal(ledgerMinorText(0, "JPY"), "0 JPY minor units");
  assert.equal(ledgerMinorText(125, null), "125 UNKNOWN CURRENCY minor units");
  assert.match(ledgerQuantityText(usageEntry), /UNKNOWN.*provider omitted usage/);
  assert.equal(ledgerQuantityText({ ...usageEntry, quantity_status: "KNOWN" }), "0 tokens");
  assert.match(ledgerSummary(usageView).total, /^UNKNOWN/);
  assert.equal(usageSummary(usageView)?.knownSubtotal, 125);
  assert.equal(usageSummary(usageView)?.total, null);
  assert.equal(usageSummary(null), null);
  assert.equal(taskProgress(null), null);
  assert.equal(taskProgress([])?.ratio, undefined);
});

test("provenance edges come only from DTO references and do not upgrade claim status", () => {
  const model = buildProvenance(claimsView, [evidenceRecord]);
  assert.equal(model.nodes.find((node) => node.kind === "claim")?.status, "PROPOSED");
  assert.deepEqual(model.edges.map((edge) => edge.label),
    ["source_ref", "artifact_id", "SUPPORTS"]);
  assert.equal(model.nodes.find((node) => node.kind === "source")?.status, "REFERENCE ONLY");
  const graph = layoutProvenance(model);
  assert.ok(graph.nodes.every((node) => Number.isFinite(node.x) && Number.isFinite(node.y)));
});

test("unresolved evidence remains visibly unresolved, without a fabricated source edge", () => {
  const model = buildProvenance(claimsView, null);
  assert.equal(model.edges.length, 1);
  assert.equal(model.nodes.find((node) => node.kind === "evidence")?.status,
    "REFERENCE NOT RESOLVED");
  assert.equal(model.nodes.some((node) => node.kind === "source"), false);
});

test("mismatched relation target is reported, not connected by display text", () => {
  const claim = claimsView.claims[0];
  assert.ok(claim);
  const model = buildProvenance({ ...claimsView, claims: [{ ...claim, relations: [
    { claim_id: "other-claim", evidence_id: evidenceRecord.id, relation: "SUPPORTS", strength: 1 },
  ] }] }, []);
  assert.equal(model.edges.length, 0);
  assert.match(model.issues[0] ?? "", /other-claim/);
});

test("SSE parser validates run identity, types and payload before exposing an event", () => {
  assert.deepEqual(parseRunEventFrame(JSON.stringify(eventFrame), "run-one"), eventFrame);
  assert.equal(parseRunEventFrame(JSON.stringify(eventFrame), "another-run"), null);
  for (const invalid of [null, [], "bad", { ...eventFrame, actor: {} },
    { ...eventFrame, payload: [] }, { ...eventFrame, event_id: "" }]) {
    assert.equal(parseRunEventFrame(JSON.stringify(invalid), "run-one"), null);
  }
  assert.equal(parseRunEventFrame("{not json", "run-one"), null);
});

test("inherit clears model references; explicit model cannot become null", () => {
  assert.deepEqual(editedModelBinding("INHERIT", "model-one"), { mode: "INHERIT", value: null });
  assert.deepEqual(editedModelBinding("EXPLICIT_MODEL", " model-one "), {
    mode: "EXPLICIT_MODEL", value: "model-one",
  });
  assert.throws(() => editedModelBinding("EXPLICIT_MODEL", " "));
});
