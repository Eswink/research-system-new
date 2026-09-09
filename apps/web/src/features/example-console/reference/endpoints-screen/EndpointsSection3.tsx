import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../EndpointsScreen.module.css";

interface EndpointsSection3Props {
  m: FixtureTypes.Model;
}

export function EndpointsSection3({ m }: EndpointsSection3Props) {
  return (
    <div className={visual.row7}>
      {m.capabilities.map((c) => (
        <span
          key={c.name}
          title={`source: ${c.source} · confidence: ${String(c.confidence ?? "n/a")}`}
          className={visual.row8}
          style={{
            background:
              c.status === "degraded"
                ? "var(--warn-dim)"
                : c.status === "unknown"
                  ? "var(--unknown-dim)"
                  : "var(--success-dim)",
            border: `1px solid ${
              c.status === "degraded"
                ? "var(--warn-line)"
                : c.status === "unknown"
                  ? "var(--unknown-line)"
                  : "var(--success-line)"
            }`,
            color:
              c.status === "degraded"
                ? "var(--warn)"
                : c.status === "unknown"
                  ? "var(--unknown)"
                  : "var(--success)",
          }}
        >
          {c.name}
        </span>
      ))}
    </div>
  );
}
