import type { Column } from "../../components/Table";

import type {
  LineageEdgeDto,
  ProjectLineageNodeDto,
  ProjectLineageResourceDto,
} from "../../api/types";

/**
 * 项目级血缘列（G9）。节点列额外标出**共享**（多个 run 贡献同一节点 = 跨 run 关系）
 * 与贡献 run 列表——跨 run 关系只由共享节点表达，不猜测连边。
 */
export function projectNodeColumns(zh: boolean): Column<ProjectLineageNodeDto>[] {
  return [
    { key: "kind", header: zh ? "类型" : "Kind", width: "110px", render: (row) => row.kind },
    { key: "label", header: zh ? "标签" : "Label", render: (row) => row.label },
    {
      key: "id",
      header: "ID",
      render: (row) => <span className="mono">{row.id}</span>,
    },
    {
      key: "runs",
      header: zh ? "贡献运行" : "Runs",
      width: "200px",
      render: (row) => (
        <span className={row.shared ? "mono" : ""}>
          {row.run_ids.length}
          {row.shared ? (zh ? "（共享）" : " (shared)") : ""}
        </span>
      ),
    },
  ];
}

/** 库资源列（未连边清单：资源与 run 的引用关系无记录面）。 */
export function projectResourceColumns(zh: boolean): Column<ProjectLineageResourceDto>[] {
  return [
    { key: "kind", header: zh ? "类型" : "Kind", width: "110px", render: (row) => row.kind },
    { key: "name", header: zh ? "名称" : "Name", render: (row) => row.name },
    {
      key: "status",
      header: zh ? "状态" : "Status",
      width: "110px",
      render: (row) => row.status,
    },
  ];
}

/** 项目级血缘边列（与 run 级同一套关系名）。 */
export function projectEdgeColumns(zh: boolean): Column<LineageEdgeDto>[] {
  return [
    {
      key: "source",
      header: zh ? "来源" : "Source",
      render: (row) => <span className="mono">{row.source}</span>,
    },
    {
      key: "relation",
      header: zh ? "关系" : "Relation",
      width: "140px",
      render: (row) => row.relation,
    },
    {
      key: "target",
      header: zh ? "目标" : "Target",
      render: (row) => <span className="mono">{row.target}</span>,
    },
  ];
}
