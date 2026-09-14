import type { LibraryResourceDto, ResourceKind } from "../../api/types";
import { Chip } from "../../components/Chip";
import type { Column } from "../../components/Table";

/** 库条目表格列（kind 参数化；拆分以守 50 行函数限制）。 */
export function libraryColumns(kind: ResourceKind, zh: boolean): Column<LibraryResourceDto>[] {
  const base: Column<LibraryResourceDto>[] = [
    { key: "name", header: zh ? "名称" : "Name", render: (row) => row.name },
    {
      key: "description",
      header: zh ? "描述" : "Description",
      render: (row) => row.description || "—",
    },
    {
      key: "tags",
      header: zh ? "标签" : "Tags",
      width: "180px",
      render: (row) => (row.tags.length === 0 ? "—" : row.tags.join(", ")),
    },
    {
      key: "status",
      header: zh ? "状态" : "Status",
      width: "120px",
      render: (row) => (
        <Chip tone={row.status === "ACTIVE" ? "accent" : "warn"}>{row.status}</Chip>
      ),
    },
  ];
  if (kind === "notebook") {
    return base;
  }
  // prompts/datasets 额外展示内容引用（不解析、不下载，仅目录事实）。
  return [
    ...base,
    {
      key: "content_ref",
      header: zh ? "内容引用" : "Content ref",
      render: (row) => <span className="mono">{row.content_ref ?? "—"}</span>,
    },
  ];
}
