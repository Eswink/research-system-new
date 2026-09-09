import FIX_CLAIMS from "../data/claims.json";
import { BarSeries } from "../reference/BarSeries";
import { Panel } from "./Panel";
import visual from "./PanelClaimsFlow.module.css";

/** Reference: Command Center.html; every metric is a fixed example. */
export const PanelClaimsFlow = () => {
  const counts: Record<string, number> = { PROPOSED: 0, VERIFIED: 0, DISPUTED: 0, REFUTED: 0 };
  FIX_CLAIMS.forEach((c) => (counts[c.status] = (counts[c.status] ?? 0) + 1));
  return <PanelClaimsFlowPanel {...{ counts }} />;
};

interface PanelClaimsFlowPanelProps {
  counts: Record<string, number>;
}

function PanelClaimsFlowPanel({ counts }: PanelClaimsFlowPanelProps) {
  return (
    <Panel
      kicker="EVIDENCE"
      title="Claims Pipeline · Real-time"
      right={<span className={visual.caption}>{FIX_CLAIMS.length} tracked</span>}
      className={visual.surface}
    >
      <div className={visual.grid}>
        {(
          [
            ["PROPOSED", counts.PROPOSED, "var(--fg-muted)"],
            ["VERIFIED", counts.VERIFIED, "var(--success)"],
            ["DISPUTED", counts.DISPUTED, "var(--warn)"],
            ["REFUTED", counts.REFUTED, "var(--danger)"],
          ] as const
        ).map(([k, v, c]) => (
          <div key={k} className={visual.surface2} style={{ border: `1px solid ${c}22` }}>
            <div className={visual.label} style={{ color: c }}>
              {v}
            </div>
            <div className={visual.caption2}>{k}</div>
          </div>
        ))}
      </div>
      <div className={visual.surface3}>
        <div className={visual.caption3}>PIPELINE FLOW · LAST 24H</div>
        <BarSeries
          data={Array.from({ length: 12 }, (_, i) => ({
            label: `${(i * 2).toString().padStart(2, "0")}h`,
            values: [
              Math.round(Math.sin(i * 0.5) * 3 + 4),
              Math.round(Math.cos(i * 0.4) * 2 + 3),
              (Math.abs(Math.sin(i)) * 2) | 0,
            ],
          }))}
          series={[
            { key: "proposed", color: "var(--fg-muted)" },
            { key: "verified", color: "var(--success)" },
            { key: "disputed", color: "var(--warn)" },
          ]}
          width={480}
          height={110}
        />
      </div>
    </Panel>
  );
}
