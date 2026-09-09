import type { Project } from "./exampleTypes";

export interface ProjectDraft {
  name: string;
  slug: string;
  template: string;
  tags: string[];
  budget: string;
  autonomy: string;
  notes: string;
}

export function initialProjectDraft(project?: Project): ProjectDraft {
  return {
    name: project?.name ?? "",
    slug: project?.slug ?? "",
    template: project?.team_template ?? "STANDARD",
    tags: project?.tags ?? [],
    budget: String(project === undefined ? 5 : project.budget_minor / 100000),
    autonomy: project?.autonomy ?? "GUARDED_AUTONOMOUS",
    notes: project?.notes ?? "",
  };
}

/** Reference currency scale is illustrative; no production Ledger receives this value. */
export function projectFromDraft(
  draft: ProjectDraft,
  previous: Project | undefined,
  identity: { id: string; now: string },
): Project {
  const amount = Number(draft.budget);
  if (draft.name.trim() === "" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(draft.slug)) {
    throw new Error("Name and lowercase kebab-case slug are required.");
  }
  const minor = Math.round(amount * 100000);
  if (!Number.isSafeInteger(minor) || minor <= 0) {
    throw new Error("The example budget must be a positive finite amount.");
  }
  const base: Project = previous ?? {
    id: identity.id,
    created_at: identity.now,
    updated_at: identity.now,
    name: "",
    slug: "",
    status: "DRAFT",
    health: null,
    owner: "EXAMPLE",
    team_template: "STANDARD",
    tags: [],
    budget_minor: 0,
    spent_minor: 0,
    runs: 0,
    active_agents: 0,
    favorited: false,
    claims: { verified: 0, disputed: 0, proposed: 0, refuted: 0 },
  };
  return {
    ...base,
    name: draft.name.trim(),
    slug: draft.slug,
    team_template: draft.template,
    tags: [...draft.tags],
    budget_minor: minor,
    updated_at: identity.now,
    autonomy: draft.autonomy,
    notes: draft.notes,
  };
}
