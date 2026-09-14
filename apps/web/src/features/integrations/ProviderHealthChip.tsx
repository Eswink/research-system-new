import { Chip } from "../../components/Chip";

/** Provider 三态健康呈现（HEALTHY/DEGRADED/UNKNOWN 等如实显示，不美化）。 */
export function ProviderHealthChip({ health }: { health: string }) {
  const tone = health === "HEALTHY" ? "accent" : health === "DEGRADED" ? "warn" : "warn";
  return <Chip tone={tone}>{health}</Chip>;
}
