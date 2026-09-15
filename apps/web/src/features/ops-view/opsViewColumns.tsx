import { api } from "../../api/client";
import type {
  AlertItemDto,
  AlertRuleDto,
  DataHealthMetricDto,
  IncidentCandidateDto,
  IncidentItemDto,
  ScheduleEntryDto,
} from "../../api/types";
import { Chip } from "../../components/Chip";
import type { Column } from "../../components/Table";
import { DeclareCandidateButton, IncidentActions } from "./IncidentActions";
import { EnabledChip } from "./EnabledChip";
import styles from "./OpsActions.module.css";
import { useAsyncAction } from "../../hooks/useAsyncAction";

/** ops 投影各页表格列（拆分以守 50 行函数限制）。 */

export function alertColumns(zh: boolean): Column<AlertItemDto>[] {
  return [
    { key: "kind", header: zh ? "类型" : "Kind", width: "170px", render: (row) => row.kind },
    {
      key: "severity",
      header: zh ? "级别" : "Severity",
      width: "120px",
      render: (row) => (
        <Chip tone={row.severity === "CRITICAL" ? "warn" : "accent"}>{row.severity}</Chip>
      ),
    },
    {
      key: "subject",
      header: zh ? "主体" : "Subject",
      render: (row) => <span className="mono">{row.subject}</span>,
    },
    { key: "detail", header: zh ? "详情" : "Detail", render: (row) => row.detail },
    {
      key: "state",
      header: zh ? "状态" : "State",
      width: "200px",
      render: (row) => <AlertStateCell row={row} zh={zh} />,
    },
  ];
}

/** 静音只加标记、不隐藏；已登记事故的来源 run 回链事故 id（写面被消费的证据）。 */
function AlertStateCell({ row, zh }: { row: AlertItemDto; zh: boolean }) {
  if (row.muted) {
    return (
      <span data-testid="alert-muted">
        <Chip tone="warn">{zh ? "已静音" : "muted"}</Chip>{" "}
        <span className="mono">{row.muted_by ?? ""}</span>
      </span>
    );
  }
  if (row.incident_id !== null) {
    return (
      <span className="mono" data-testid="alert-incident">
        {row.incident_id}
      </span>
    );
  }
  return <span>—</span>;
}

export function ruleColumns(zh: boolean, onChanged: () => void): Column<AlertRuleDto>[] {
  return [
    { key: "name", header: zh ? "名称" : "Name", render: (row) => row.name },
    {
      key: "scope",
      header: zh ? "适用范围" : "Scope",
      width: "230px",
      render: (row) => `${row.kind ?? "ALL"} · ${row.max_severity ?? "ANY"}`,
    },
    {
      key: "enabled",
      header: zh ? "启用" : "Enabled",
      width: "100px",
      render: (row) => <EnabledChip enabled={row.enabled} />,
    },
    {
      key: "actions",
      header: zh ? "操作" : "Actions",
      width: "190px",
      render: (row) => <RuleRowActions rule={row} zh={zh} onDone={onChanged} />,
    },
  ];
}

function RuleRowActions({
  rule,
  zh,
  onDone,
}: {
  rule: AlertRuleDto;
  zh: boolean;
  onDone: () => void;
}) {
  const action = useAsyncAction(onDone);
  return (
    <span className={styles.row} data-testid="alert-rule-actions">
      <button
        className="btn sm ghost"
        type="button"
        disabled={action.busy}
        onClick={() => {
          action.run(() => api.patchAlertRule(rule.id, { enabled: !rule.enabled }));
        }}
      >
        {rule.enabled ? (zh ? "停用" : "Disable") : zh ? "启用" : "Enable"}
      </button>
      <button
        className="btn sm danger"
        type="button"
        disabled={action.busy}
        onClick={() => {
          action.run(() => api.deleteAlertRule(rule.id));
        }}
      >
        {zh ? "删除" : "Delete"}
      </button>
    </span>
  );
}

export function incidentCandidateColumns(
  zh: boolean,
  onChanged: () => void,
): Column<IncidentCandidateDto>[] {
  return [
    {
      key: "run_id",
      header: "Run",
      render: (row) => <span className="mono">{row.run_id}</span>,
    },
    { key: "protocol_id", header: "Protocol", render: (row) => row.protocol_id },
    {
      key: "state",
      header: zh ? "状态" : "State",
      width: "110px",
      render: (row) => <Chip tone="warn">{row.state}</Chip>,
    },
    { key: "updated_at", header: zh ? "更新时间" : "Updated", render: (row) => row.updated_at },
    {
      key: "actions",
      header: zh ? "登记" : "Declare",
      width: "170px",
      render: (row) => <DeclareCandidateButton candidate={row} zh={zh} onDone={onChanged} />,
    },
  ];
}

export function declaredIncidentColumns(
  zh: boolean,
  onChanged: () => void,
): Column<IncidentItemDto>[] {
  return [
    { key: "title", header: zh ? "标题" : "Title", render: (row) => row.title },
    {
      key: "severity",
      header: zh ? "级别" : "Severity",
      width: "120px",
      render: (row) => (
        <Chip tone={row.severity === "CRITICAL" ? "warn" : "accent"}>{row.severity}</Chip>
      ),
    },
    {
      key: "status",
      header: zh ? "状态" : "Status",
      width: "130px",
      render: (row) => <Chip tone={row.status === "CLOSED" ? "accent" : "warn"}>{row.status}</Chip>,
    },
    {
      key: "run_id",
      header: "Run",
      width: "180px",
      render: (row) => <span className="mono">{row.run_id ?? "—"}</span>,
    },
    {
      key: "assignee",
      header: zh ? "处理人" : "Assignee",
      width: "140px",
      render: (row) => row.assignee ?? "—",
    },
    {
      key: "actions",
      header: zh ? "处置" : "Disposition",
      width: "420px",
      render: (row) => <IncidentActions incident={row} zh={zh} onDone={onChanged} />,
    },
  ];
}

export function scheduleColumns(zh: boolean): Column<ScheduleEntryDto>[] {
  return [
    { key: "name", header: zh ? "名称" : "Name", render: (row) => row.name },
    {
      key: "interval",
      header: zh ? "间隔（秒）" : "Interval (s)",
      width: "140px",
      render: (row) => String(row.interval_seconds),
    },
    { key: "purpose", header: zh ? "用途" : "Purpose", render: (row) => row.purpose },
    {
      key: "enabled",
      header: zh ? "启用" : "Enabled",
      width: "100px",
      render: (row) => <EnabledChip enabled={row.enabled} />,
    },
  ];
}

export function dataHealthColumns(zh: boolean): Column<DataHealthMetricDto>[] {
  return [
    { key: "metric", header: zh ? "指标" : "Metric", render: (row) => row.metric },
    { key: "value", header: zh ? "值" : "Value", width: "180px", render: (row) => row.value },
    {
      key: "status",
      header: zh ? "状态" : "Status",
      width: "140px",
      render: (row) => (
        <Chip tone={row.status === "OK" || row.status === "INFO" ? "accent" : "warn"}>
          {row.status}
        </Chip>
      ),
    },
  ];
}
