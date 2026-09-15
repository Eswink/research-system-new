import { useState } from "react";

import { api } from "../../api/client";
import type { AlertRuleDto } from "../../api/types";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, ErrorState, UnavailableState } from "../../components/States";
import { Table } from "../../components/Table";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { InlineSelect, InlineTextInput } from "../../components/InlineFields";
import { ruleColumns } from "./opsViewColumns";
import { useAsyncAction } from "../../hooks/useAsyncAction";

const KINDS = ["RUN_FAILED", "ENDPOINT_DEGRADED", "WORKER_OFFLINE"] as const;
const SEVERITIES = ["CRITICAL", "WARNING", "INFO"] as const;

/**
 * 告警静音规则（G7 / POST|PATCH|DELETE /ops/alert-rules）。
 *
 * 规则是**被消费**的：命中规则的告警在读面带 `muted=true` + `muted_by`，
 * 但**不会从列表消失**——静音不是隐藏，看不见的问题更难修。
 */
export function OpsAlertRulesPanel({ onChanged }: { onChanged: () => void }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const rules = useResource("ops-alert-rules", () => api.opsAlertRules());
  const changed = (): void => {
    rules.reload();
    onChanged();
  };
  return (
    <PanelSection
      title={zh ? "静音规则" : "Mute rules"}
      count={rules.data?.rules.length}
      extra={
        <button
          className="btn sm ghost"
          type="button"
          disabled={rules.phase === "loading"}
          onClick={rules.reload}
        >
          {zh ? "刷新" : "Refresh"}
        </button>
      }
    >
      <div data-testid="alert-rules-panel">
        <ResourceBoundary state={rules}>
          {rules.data !== null && (
            <RulesBody data={rules.data} zh={zh} onChanged={changed} />
          )}
        </ResourceBoundary>
      </div>
    </PanelSection>
  );
}

function RulesBody({
  data,
  zh,
  onChanged,
}: {
  data: { rules: AlertRuleDto[]; rules_available: boolean; rules_reason: string | null };
  zh: boolean;
  onChanged: () => void;
}) {
  return (
    <>
      {!data.rules_available && (
        <UnavailableState
          title={zh ? "规则不可用" : "Rules unavailable"}
          reason={data.rules_reason ?? ""}
        />
      )}
      {data.rules_available && <RuleCreateForm zh={zh} onCreated={onChanged} />}
      {data.rules.length === 0 ? (
        <EmptyState message={zh ? "尚无规则" : "No rules yet"} />
      ) : (
        <Table
          columns={ruleColumns(zh, onChanged)}
          rows={data.rules}
          rowKey={(row: AlertRuleDto) => row.id}
          ariaLabel={zh ? "告警静音规则" : "Alert mute rules"}
        />
      )}
    </>
  );
}

/** 新建规则：kind / max_severity 留空 = 不限来源 / 不限级别。 */
function RuleCreateForm({ zh, onCreated }: { zh: boolean; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState("");
  const [severity, setSeverity] = useState("");
  const action = useAsyncAction(onCreated);
  const submit = (): void => {
    const trimmed = name.trim();
    if (trimmed === "") return;
    action.run(() =>
      api.createAlertRule({
        name: trimmed,
        kind: kind === "" ? null : kind,
        max_severity: severity === "" ? null : severity,
      }),
    );
    setName("");
  };
  return (
    <form
      className="toolbar"
      data-testid="alert-rule-create"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <InlineTextInput
        value={name}
        onChange={setName}
        placeholder={zh ? "规则名" : "Rule name"}
      />
      <InlineSelect
        value={kind}
        onChange={setKind}
        options={KINDS}
        placeholder={zh ? "全部来源" : "All kinds"}
      />
      <InlineSelect
        value={severity}
        onChange={setSeverity}
        options={SEVERITIES}
        placeholder={zh ? "不限级别" : "Any severity"}
      />
      <button className="btn" type="submit" disabled={action.busy || name.trim() === ""}>
        {zh ? "新建规则" : "New rule"}
      </button>
      {action.error !== null && <ErrorState message={action.error} />}
    </form>
  );
}