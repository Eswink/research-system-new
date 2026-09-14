import type { LineageEdgeDto, LineageNodeDto } from "../../api/types";
import type { Column } from "../../components/Table";

/** 血缘节点列（拆分以保持 LineageProjection 函数 ≤50 行/复杂度 ≤15）。 */
export function nodeColumns(zh: boolean): Column<LineageNodeDto>[] {
  return [
    { key: "kind", header: zh ? "类型" : "Kind", width: "120px", render: (row) => row.kind },
    { key: "label", header: zh ? "标签" : "Label", render: (row) => row.label },
    {
      key: "id",
      header: "ID",
      render: (row) => <span className="mono">{row.id}</span>,
    },
  ];
}

/** 血缘边列。 */
export function edgeColumns(zh: boolean): Column<LineageEdgeDto>[] {
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
