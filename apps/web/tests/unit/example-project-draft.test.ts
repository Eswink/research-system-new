import assert from "node:assert/strict";
import { test } from "node:test";
import {
  initialProjectDraft, projectFromDraft,
} from "../../src/features/example-console/projectDraft";

const identity = { id: "example-project-test", now: "2026-09-09T00:00:00Z" };

test("new example project has no borrowed production run, spending or claim counters", () => {
  const draft = { ...initialProjectDraft(), name: "My example", slug: "my-example" };
  const project = projectFromDraft(draft, undefined, identity);
  assert.equal(project.status, "DRAFT");
  assert.equal(project.health, null);
  assert.equal(project.runs, 0);
  assert.equal(project.spent_minor, 0);
  assert.deepEqual(Object.values(project.claims), [0, 0, 0, 0]);
});

test("editing an example preserves its identity and unrelated counters", () => {
  const draft = { ...initialProjectDraft(), name: "Before", slug: "before" };
  const project = projectFromDraft(draft, undefined, identity);
  const next = projectFromDraft({ ...draft, name: "After", notes: "local note" }, project, {
    ...identity, id: "must-not-replace-id",
  });
  assert.equal(next.name, "After");
  assert.equal(next.id, project.id);
  assert.equal(next.notes, "local note");
  assert.equal(project.name, "Before");
});

test("invalid names, slugs and budgets do not create local projects", () => {
  const draft = { ...initialProjectDraft(), name: "Example", slug: "valid-slug" };
  for (const patch of [{ name: " " }, { slug: "Invalid/Slug" },
    { budget: "NaN" }, { budget: "-1" }, { budget: "Infinity" }, { budget: "0" }]) {
    assert.throws(() => projectFromDraft({ ...draft, ...patch }, undefined, identity));
  }
});
