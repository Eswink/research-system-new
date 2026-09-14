import type { ToolProviderDto } from "../../api/types";
import type { Column } from "../../components/Table";
import { ProviderHealthChip } from "./ProviderHealthChip";

/** Tool Provider 表格列（integrations 页；拆分以保持页面函数 ≤50 行）。 */
export function providerColumns(zh: boolean): Column<ToolProviderDto>[] {
  return [
    { key: "id", header: zh ? "提供者" : "Provider", render: (row) => row.id },
    { key: "kind", header: zh ? "类型" : "Kind", width: "120px", render: (row) => row.kind },
    {
      key: "trust",
      header: zh ? "信任级" : "Trust",
      width: "150px",
      render: (row) => row.trust_level,
    },
    {
      key: "capabilities",
      header: zh ? "能力" : "Capabilities",
      render: (row) => <span className="mono">{row.capabilities.join(", ")}</span>,
    },
    {
      key: "health",
      header: zh ? "健康" : "Health",
      width: "130px",
      render: (row) => <ProviderHealthChip health={row.health} />,
    },
  ];
}
