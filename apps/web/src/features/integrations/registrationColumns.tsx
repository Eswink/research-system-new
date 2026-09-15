import type { ToolProviderRegistrationDto } from "../../api/types";
import type { Column } from "../../components/Table";
import { RegistryActions } from "./RegistryActions";

/** 注册表列（integrations 页；动作列与 provider 目录列分离以保持函数 ≤50 行）。 */
export function registrationColumns(
  zh: boolean,
  onChanged: () => void,
): Column<ToolProviderRegistrationDto>[] {
  return [
    { key: "id", header: zh ? "注册项" : "Registration", render: (row) => row.id },
    { key: "kind", header: zh ? "类型" : "Kind", width: "120px", render: (row) => row.kind },
    {
      key: "state",
      header: zh ? "状态" : "State",
      width: "170px",
      render: (row) => (
        <span className="mono" data-testid={`registry-state-${row.state}`}>
          {row.state} · {row.trust_level}
        </span>
      ),
    },
    {
      key: "pin",
      header: zh ? "pin" : "Pin",
      render: (row) => <span className="mono">{row.pinned_revision.slice(0, 19)}…</span>,
    },
    {
      key: "catalog",
      header: zh ? "目录" : "Catalog",
      width: "110px",
      render: (row) =>
        row.catalog_active ? (zh ? "已生效" : "active") : zh ? "未生效" : "not active",
    },
    {
      key: "health",
      header: zh ? "最近复核" : "Last check",
      width: "190px",
      render: (row) => (
        <span className="mono" data-testid={`registry-health-${row.id}`}>
          {row.last_health ?? "—"}
          {row.health_detail !== null && ` · ${row.health_detail}`}
        </span>
      ),
    },
    {
      key: "actions",
      header: zh ? "处置" : "Actions",
      render: (row) => <RegistryActions registration={row} zh={zh} onDone={onChanged} />,
    },
  ];
}
