import { type Dispatch, type SetStateAction } from "react";
import FIX_AGENTS from "../../data/agents.json";
import FIX_MODELS from "../../data/models.json";
import FIX_ROLES from "../../data/roles.json";
import { Icon } from "../Icon";
import visual from "../TeamScreen.module.css";
import { TeamSection5 } from "./TeamSection5";
import { TeamSection7 } from "./TeamSection7";

interface TeamSection4Props {
  modelUsage: Record<string, string[]>;
  setSelectedAgent: Dispatch<SetStateAction<string | null>>;
  selectedAgent: string | null;
  t: (key: string, fallback?: string) => string;
}

export function TeamSection4({
  modelUsage,
  setSelectedAgent,
  selectedAgent,
  t,
}: TeamSection4Props) {
  return (
    <div className={visual.grid3}>
      {FIX_AGENTS.map((a) => {
        const role = FIX_ROLES.find((r) => r.id === a.role_id);
        const modelId = a.model_binding.model_id ?? a.resolved_model_id ?? "unbound";
        const model = FIX_MODELS.find((m) => m.id === modelId);
        const shares = modelUsage[modelId]?.filter((id) => id !== a.id) ?? [];
        const isConflict = a.id === "ag_ethics_01"; // preflight-flagged heterogeneity
        return (
          <div
            key={a.id}
            onClick={() => {
              setSelectedAgent(a.id);
            }}
            className={visual.surface8}
            style={{
              border: `1px solid ${
                isConflict
                  ? "var(--warn-line)"
                  : selectedAgent === a.id
                    ? "var(--accent)"
                    : "var(--border)"
              }`,
            }}
          >
            <TeamSection5 {...{ a, role, isConflict }} />
            <TeamSection7 {...{ model, a, t }} />
            {shares.length > 0 && (
              <div
                className={visual.row14}
                style={{ color: isConflict ? "var(--warn)" : "var(--fg-faint)" }}
              >
                <Icon name="graph" size={9} /> {t("tm.sharesWith")} {shares.length} {t("tm.agent")}
                {shares.length > 1 ? t("tm.agents2") : ""}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
