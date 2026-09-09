import type { AgentSpecDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { EmptyState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";
import { bindingDescription } from "./modelBinding";

export function AgentCards({
  agents,
  onEdit,
}: {
  agents: AgentSpecDto[];
  onEdit: (id: string) => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  if (agents.length === 0) {
    return (
      <div data-testid="agents-empty">
        <EmptyState message={zh ? "没有匹配的 Agent 实例" : "No matching configured agents"} />
      </div>
    );
  }
  return (
    <div className={styles.cards}>
      {agents.map((agent) => (
        <AgentCard key={agent.id} agent={agent} onEdit={onEdit} zh={zh} />
      ))}
    </div>
  );
}

function AgentCard({
  agent,
  onEdit,
  zh,
}: {
  agent: AgentSpecDto;
  onEdit: (id: string) => void;
  zh: boolean;
}) {
  return (
    <article className={styles.card} data-testid="agent-row">
      <div className={styles.cardHead}>
        <h2 className={styles.cardTitle}>{agent.id}</h2>
        <Chip>{agent.role}</Chip>
      </div>
      <KeyValueList
        fields={[
          { label: "Binding", value: bindingDescription(agent.model_binding) },
          { label: "Runtime", value: agent.runtime_kind ?? "INHERIT" },
        ]}
      />
      <button
        type="button"
        className="btn sm"
        onClick={() => {
          onEdit(agent.id);
        }}
      >
        {zh ? "编辑绑定" : "Edit binding"}
      </button>
    </article>
  );
}
