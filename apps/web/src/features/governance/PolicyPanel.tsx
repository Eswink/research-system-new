import { api } from "../../api/client";
import type { GateCapabilityViewDto, PolicyCapabilitiesDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { Table, type Column } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

/** 策略面只读快照（WP-C PLAN-049）：声明规则 + 门链能力逐 scope 有效判决。 */
export function PolicyPanel() {
  const { language } = useI18n();
  const zh = language === "zh";
  const view = useResource("policy-capabilities", () => api.policyCapabilities());
  return (
    <PanelSection
      title={zh ? "能力策略（只读）" : "Capability policy (read-only)"}
      extra={<Chip tone="neutral">{view.data?.source ?? "policy.yaml"}</Chip>}
    >
      {view.error !== null && <EmptyState message={view.error} />}
      {view.data !== null && <PolicyBody view={view.data} zh={zh} />}
    </PanelSection>
  );
}

function PolicyBody({ view, zh }: { view: PolicyCapabilitiesDto; zh: boolean }) {
  return (
    <div data-testid="policy-panel">
      <KeyValueList
        fields={[
          { label: zh ? "策略 ID" : "Policy id", value: view.policy_id },
          { label: zh ? "版本" : "Version", value: view.version },
          { label: zh ? "默认判决" : "Default effect", value: view.default_effect },
          { label: zh ? "声明规则" : "Declared rules", value: String(view.rules.length) },
        ]}
      />
      {view.gate_capabilities.map((gate) => (
        <GateCapabilityTable key={gate.capability} gate={gate} zh={zh} />
      ))}
      <p className={styles.notice}>{view.note}</p>
    </div>
  );
}

/** 逐 scope 有效判决表：UNKNOWN 表示策略面不可用，不渲染成 ALLOW。 */
function GateCapabilityTable({ gate, zh }: { gate: GateCapabilityViewDto; zh: boolean }) {
  const columns: Column<string>[] = [
    { key: "scope", header: "scope", render: (scope) => <span className="mono">{scope}</span> },
    {
      key: "effect",
      header: zh ? "有效判决" : "Effective decision",
      render: (scope) => <EffectChip effect={gate.effects[scope]} />,
    },
    {
      key: "reason",
      header: zh ? "依据" : "Basis",
      render: (scope) => gate.reasons[scope] ?? "—",
    },
  ];
  return (
    <div data-testid="gate-capability">
      <Chip tone="accent">{gate.capability}</Chip>
      <Table
        columns={columns}
        rows={gate.scopes}
        rowKey={(scope) => `${gate.capability}:${scope}`}
        ariaLabel={gate.capability}
        empty={<EmptyState message={zh ? "无 scope 声明" : "No declared scope"} />}
      />
    </div>
  );
}

function EffectChip({ effect }: { effect: string | undefined }) {
  if (effect === undefined) return <Chip tone="unknown">UNKNOWN</Chip>;
  return <Chip tone={effect === "ALLOW" ? "success" : "warn"}>{effect}</Chip>;
}
