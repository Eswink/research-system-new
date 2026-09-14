import type {
  AlertItemDto,
  DataHealthMetricDto,
  IncidentItemDto,
  ScheduleEntryDto,
} from "../../api/types";
import { Chip } from "../../components/Chip";
import type { Column } from "../../components/Table";

/** ops 只读投影各页表格列（拆分以守 50 行函数限制）。 */

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
  ];
}

export function incidentColumns(zh: boolean): Column<IncidentItemDto>[] {
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
      render: (row) => (
        <Chip tone={row.enabled ? "accent" : "warn"}>{row.enabled ? "ON" : "OFF"}</Chip>
      ),
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
