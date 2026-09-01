import type { ModelCatalog } from "./types.ts";

export type ModelPreflight =
  | { readonly ok: true; readonly modelId: string; readonly displayName: string }
  | { readonly ok: false; readonly modelId: string; readonly reason: string };

/**
 * Fail-closed model verification: the requested id must exist verbatim in the
 * account catalog. Model drift is detected again after each run by comparing
 * the run's resolved model with this id.
 */
export async function verifyModel(catalog: ModelCatalog, modelId: string): Promise<ModelPreflight> {
  let entries: readonly { id: string; displayName: string }[];
  try {
    entries = await catalog.list();
  } catch {
    return { ok: false, modelId, reason: "model_catalog_unavailable" };
  }
  const match = entries.find((entry) => entry.id === modelId);
  if (match !== undefined) {
    return { ok: true, modelId: match.id, displayName: match.displayName };
  }
  const known = entries
    .map((entry) => entry.id)
    .sort()
    .join(",");
  return { ok: false, modelId, reason: `model_not_in_catalog; available: [${known}]` };
}
