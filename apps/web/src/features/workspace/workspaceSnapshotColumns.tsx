import type { WorkspaceSnapshotChangeDto, WorkspaceSnapshotFileDto } from "../../api/types";
import type { Column } from "../../components/Table";

export function snapshotFileColumns(zh: boolean): Column<WorkspaceSnapshotFileDto>[] {
  return [
    {
      key: "path",
      header: zh ? "路径" : "Path",
      render: (row) => <span className="mono">{row.path}</span>,
    },
    {
      key: "size",
      header: zh ? "大小（字节）" : "Size (bytes)",
      width: "140px",
      align: "right",
      render: (row) => String(row.size_bytes),
    },
    {
      key: "sha256",
      header: "sha256",
      width: "220px",
      render: (row) => <span className="mono">{shortHash(row.sha256)}</span>,
    },
  ];
}

export function snapshotChangeColumns(zh: boolean): Column<WorkspaceSnapshotChangeDto>[] {
  return [
    {
      key: "kind",
      header: zh ? "变化" : "Change",
      width: "120px",
      render: (row) => <span data-testid="snapshot-change-kind">{row.kind}</span>,
    },
    {
      key: "path",
      header: zh ? "路径" : "Path",
      render: (row) => <span className="mono">{row.path}</span>,
    },
    {
      key: "left",
      header: zh ? "左侧（大小 / sha256）" : "Left (size / sha256)",
      width: "240px",
      render: (row) => sideText(row.left_size_bytes, row.left_sha256),
    },
    {
      key: "right",
      header: zh ? "右侧（大小 / sha256）" : "Right (size / sha256)",
      width: "240px",
      render: (row) => sideText(row.right_size_bytes, row.right_sha256),
    },
  ];
}

function sideText(size: number | null, sha: string | null): string {
  if (size === null || sha === null) return "—";
  return `${String(size)} / ${shortHash(sha)}`;
}

/** 只展示摘要前缀：完整 sha256 在表格里既不可读也挤掉其它列。 */
export function shortHash(sha: string): string {
  return sha.length <= 16 ? sha : `${sha.slice(0, 16)}…`;
}

/** digest 前缀（`sha256:` 之后的 hex 前 12 位）用于选择器与摘要。 */
export function shortDigest(digest: string): string {
  const hex = digest.split(":", 2)[1] ?? digest;
  return `${hex.slice(0, 12)}…`;
}
