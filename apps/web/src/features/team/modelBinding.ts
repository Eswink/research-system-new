import type { AgentSpecDto } from "../../api/types";

export type EditableBindingMode = "INHERIT" | "EXPLICIT_MODEL";

/** Domain contract: EXPLICIT_MODEL cannot contain null; INHERIT cannot carry a model/profile ID. */
export function editedModelBinding(mode: EditableBindingMode, modelId: string) {
  if (mode === "INHERIT") return { mode, value: null };
  if (modelId.trim() === "") throw new Error("An explicit model binding requires a model ID");
  return { mode, value: modelId.trim() };
}

export function bindingDescription(binding: AgentSpecDto["model_binding"]): string {
  return `${binding.mode} · ${binding.value ?? "—"}`;
}
