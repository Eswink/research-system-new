import { Heatmap } from "../reference/Heatmap";
import { Panel } from "./Panel";
import visual from "./PanelModelActivity.module.css";

/** Reference: Command Center.html; every metric is a fixed example. */
export const PanelModelActivity = () => {
  // Deterministic hourly heatmap 24h × 6 hours grouping
  const grid = Array.from({ length: 5 }, (_, y) =>
    Array.from({ length: 24 }, (_, x) =>
      Math.max(0, Math.min(1, (Math.sin(x * 0.4 + y) + Math.cos(x * 0.2 + y * 1.4)) * 0.4 + 0.5)),
    ),
  );
  const labels = ["gpt-4o", "sonnet-4", "opus-4.1", "gemini-2.5", "qwen3-235b"];
  return (
    <Panel kicker="MODELS" title="Activity Heatmap · 24h × Model" className={visual.surface}>
      <Heatmap
        data={grid}
        yLabels={labels}
        xLabels={Array.from({ length: 24 }, (_, i) =>
          i % 4 === 0 ? String(i).padStart(2, "0") : "",
        )}
        cell={14}
        gap={2}
      />
      <div className={visual.row}>
        <span>less</span>
        {[0.1, 0.3, 0.5, 0.7, 0.9].map((v) => (
          <div key={v} className={visual.indicator} style={{ opacity: v }} />
        ))}
        <span>more</span>
        <span className={visual.surface2}>peak: 09:00-11:00 JST</span>
      </div>
    </Panel>
  );
};
