import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../IntegrationsScreen.module.css";
import { StatusBadge } from "../StatusBadge";

interface IntegrationsStatConnected2Props {
  int: FixtureTypes.Integration;
  t: (key: string, fallback?: string) => string;
}

export function IntegrationsStatConnected2({ int, t }: IntegrationsStatConnected2Props) {
  return (
    <div className={visual.row3}>
      {int.status === "connected" && (
        <StatusBadge tone="success" icon="check" label={t("in.stat.connected")} size="sm" filled />
      )}
      {int.status === "available" && (
        <StatusBadge
          tone="neutral"
          icon="circle-o"
          label={t("in.stat.available")}
          size="sm"
          dashed
        />
      )}
      {int.status === "disconnected" && (
        <StatusBadge tone="danger" icon="x" label={t("in.stat.disconnected")} size="sm" />
      )}
      {int.health === "degraded" && (
        <StatusBadge tone="warn" icon="warn-tri" label={t("in.stat.degraded")} size="sm" />
      )}
    </div>
  );
}
