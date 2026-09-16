import type { ToolProviderRegistrationDto } from "../../api/types";

/** 指纹在行内只做"可比对"用：截到 12 位 hex 足够人眼区分，完整值仍在 DTO 里。 */
function shortDigest(digest: string | null): string {
  if (digest === null) {
    return "?";
  }
  const hex = digest.startsWith("sha256:") ? digest.slice("sha256:".length) : digest;
  return hex.slice(0, 12);
}

/**
 * 最近一次复核的三件事：健康三态、说明、以及**schema 是否已偏离基线**。
 *
 * 漂移是状态（当前观测 vs 基线），所以这里显示的是两个指纹的对照——
 * 只说"漂移了"而不给可比对的值，操作者仍然不知道变了什么。
 */
export function RegistryHealthCell({
  row,
  zh,
}: {
  row: ToolProviderRegistrationDto;
  zh: boolean;
}) {
  return (
    <span className="mono" data-testid={`registry-health-${row.id}`}>
      {row.last_health ?? "—"}
      {row.health_detail !== null && ` · ${row.health_detail}`}
      {row.schema_drift && (
        <span data-testid={`registry-schema-drift-${row.id}`}>
          {` · ${zh ? "schema 漂移" : "schema drift"} `}
          {shortDigest(row.schema_baseline_digest)}→{shortDigest(row.last_schema_digest)}
        </span>
      )}
    </span>
  );
}
