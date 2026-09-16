import type { ToolPackDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import type { Column } from "../../components/Table";
import { shortDigest } from "./ToolPackPendingBanner";
import { ToolPackRevokeControl } from "./ToolPackRevokeControl";

/**
 * ToolPack 表列（G15 / PLAN-065）。
 *
 * digest 列**始终是生效版本**：待批准版本的候选 digest 只出现在横幅里。
 * 若这里显示 pending digest，用户会把"已提交"读成"已生效"。
 */
export function toolPackColumns(zh: boolean, onChanged: () => void): Column<ToolPackDto>[] {
  return [
    { key: "id", header: "ToolPack", render: idCell },
    { key: "state", header: zh ? "状态" : "State", width: "170px", render: stateCell(zh) },
    {
      key: "digest",
      header: zh ? "生效 digest" : "Effective digest",
      render: digestCell,
    },
    {
      key: "version",
      header: zh ? "版本" : "Version",
      width: "90px",
      render: (row) => <span className="mono">{row.version}</span>,
    },
    {
      key: "capabilities",
      header: "capabilities",
      render: (row) => (
        <span className="mono" data-testid={`toolpack-capabilities-${row.id}`}>
          {row.capabilities.length > 0 ? row.capabilities.join(", ") : "—"}
        </span>
      ),
    },
    {
      key: "catalog",
      header: zh ? "目录" : "Catalog",
      width: "110px",
      render: (row) =>
        row.catalog_digest_active ? (zh ? "已进入" : "active") : zh ? "未进入" : "not active",
    },
    {
      key: "actions",
      header: zh ? "处置" : "Actions",
      render: (row) => <ToolPackRevokeControl pack={row} zh={zh} onChanged={onChanged} />,
    },
  ];
}

function idCell(row: ToolPackDto) {
  return (
    <span className="mono" data-testid={`toolpack-id-${row.id}`}>
      {row.id}
    </span>
  );
}

/** 状态列同时给出"有未生效候选"的事实（候选本身在横幅里展开）。 */
function stateCell(zh: boolean) {
  return (row: ToolPackDto) => (
    <span className="mono" data-testid={`toolpack-state-${row.id}`}>
      {row.state}
      {row.pending !== null && <Chip tone="warn">{zh ? "待批准" : "pending"}</Chip>}
    </span>
  );
}

function digestCell(row: ToolPackDto) {
  return (
    <span className="mono" title={row.digest} data-testid={`toolpack-digest-${row.id}`}>
      {shortDigest(row.digest)}
    </span>
  );
}
