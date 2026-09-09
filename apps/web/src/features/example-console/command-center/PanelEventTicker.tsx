import FIX_EVENTS from "../data/events.json";
import { Panel } from "./Panel";
import visual from "./PanelEventTicker.module.css";

/** Reference: Command Center.html; every metric is a fixed example. */
export const PanelEventTicker = () => (
  <Panel
    kicker="STREAM"
    title="Live SSE · Events"
    right={
      <>
        <div className={`pulse-dot ${visual.indicator ?? ""}`} />
        <span className={visual.caption}>LIVE</span>
      </>
    }
    className={visual.surface}
  >
    <div className={visual.surface2}>
      <div className={visual.surface3}>
        {[...FIX_EVENTS, ...FIX_EVENTS].map((ev, i) => (
          <div
            key={i}
            className={visual.caption2}
            style={{
              borderLeft: `2px solid ${
                ev.type.includes("failed")
                  ? "var(--danger)"
                  : ev.type.includes("gate")
                    ? "var(--warn)"
                    : "var(--accent)"
              }`,
            }}
          >
            <div className={visual.row}>
              <span className={visual.surface4}>
                {new Date(ev.occurred_at).toISOString().slice(11, 19)}
              </span>
              <span className={visual.surface5}>{ev.type}</span>
            </div>
            <div className={visual.caption3}>{ev.task_id ?? ev.scope}</div>
          </div>
        ))}
      </div>
    </div>
  </Panel>
);
