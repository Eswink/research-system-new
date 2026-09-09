import { Panel } from "./Panel";
import visual from "./PanelWorldMap.module.css";

/** Reference: Command Center.html; every metric is a fixed example. */
export const PanelWorldMap = () => {
  // Fake datacenter positions
  const dcs = [
    { name: "Tokyo · relay.lab", x: 82, y: 40, health: "ok", latency: 89 },
    { name: "us-east · OpenAI", x: 22, y: 45, health: "ok", latency: 214 },
    { name: "us-central · Vertex", x: 20, y: 52, health: "warn", latency: null },
    { name: "eu-west · Anthropic", x: 48, y: 40, health: "ok", latency: 302 },
    { name: "ap-northeast · S3", x: 84, y: 44, health: "ok", latency: 12 },
  ];
  return (
    <Panel
      kicker="INFRASTRUCTURE"
      title="Endpoint Health · Global"
      right={
        <span className={visual.caption}>
          {dcs.filter((d) => d.health === "ok").length}/{dcs.length} nominal
        </span>
      }
      className={visual.surface}
    >
      <PanelWorldMapSection {...{ dcs }} />
      <div className={visual.grid}>
        {dcs.map((d) => (
          <div key={d.name} className={visual.row}>
            <div
              className={visual.surface2}
              style={{
                background:
                  d.health === "ok"
                    ? "var(--success)"
                    : d.health === "warn"
                      ? "var(--warn)"
                      : "var(--danger)",
              }}
            />
            <span className={visual.surface3}>{d.name}</span>
            <span className={visual.surface4}>
              {d.latency != null ? `${String(d.latency)}ms` : "—"}
            </span>
          </div>
        ))}
      </div>
    </Panel>
  );
};

interface PanelWorldMapSectionProps {
  dcs: (
    | { name: string; x: number; y: number; health: string; latency: number }
    | { name: string; x: number; y: number; health: string; latency: null }
  )[];
}

function PanelWorldMapSection({ dcs }: PanelWorldMapSectionProps) {
  return (
    <div className={visual.indicator}>
      {/* Simplified world silhouette */}
      <PanelWorldMapChart {...{ dcs }} />
    </div>
  );
}

function WorldMapDots() {
  return Array.from({ length: 32 }).map((_, column) =>
    Array.from({ length: 18 }).map((__, row) => {
      const x = column * 12 + 8;
      const y = row * 12 + 8;
      const land = Math.sin(x * 0.03) + Math.cos(y * 0.05 + x * 0.02) > 0.1 && y > 30 && y < 200;
      return land ? (
        <circle
          key={`${String(column)}-${String(row)}`}
          cx={x}
          cy={y}
          r="0.9"
          fill="rgba(76, 141, 255, 0.28)"
        />
      ) : null;
    }),
  );
}

interface PanelWorldMapChartProps {
  dcs: (
    | { name: string; x: number; y: number; health: string; latency: number }
    | { name: string; x: number; y: number; health: string; latency: null }
  )[];
}

function PanelWorldMapChart({ dcs }: PanelWorldMapChartProps) {
  return (
    <svg width="100%" height="100%" viewBox="0 0 400 220" className={visual.overlay}>
      <WorldMapDots />
      {/* connections between DCs */}
      {dcs.slice(0, dcs.length - 1).map((d, i) => (
        <line
          key={i}
          x1={(d.x / 100) * 400}
          y1={(d.y / 100) * 220}
          x2={((dcs[i + 1]?.x ?? d.x) / 100) * 400}
          y2={((dcs[i + 1]?.y ?? d.y) / 100) * 220}
          stroke="rgba(76, 141, 255, 0.2)"
          strokeWidth="1"
          strokeDasharray="2 3"
        />
      ))}
      {/* DC markers */}
      {dcs.map((d, i) => {
        const cx = (d.x / 100) * 400,
          cy = (d.y / 100) * 220;
        const color = d.health === "ok" ? "#35A56F" : d.health === "warn" ? "#D9962A" : "#E0524C";
        return (
          <g key={i}>
            <circle cx={cx} cy={cy} r="8" fill={color} fillOpacity="0.2" />
            <circle cx={cx} cy={cy} r="3" fill={color}>
              <animate attributeName="r" values="3;5;3" dur="2s" repeatCount="indefinite" />
            </circle>
          </g>
        );
      })}
    </svg>
  );
}
