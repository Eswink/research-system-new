import FIX_ALERT_INBOX from "../data/alert-inbox.json";
import { StatusBadge } from "../reference/StatusBadge";
import { Panel } from "./Panel";
import visual from "./PanelAlertsFeed.module.css";

/** Reference: Command Center.html; every metric is a fixed example. */
export const PanelAlertsFeed = () => (
  <Panel
    kicker="ALERTS"
    title="Active · Firing"
    right={
      <span className={`chip ${visual.surface2 ?? ""}`}>
        {FIX_ALERT_INBOX.filter((a) => a.state === "firing").length} FIRING
      </span>
    }
    className={visual.surface}
  >
    <div className={visual.column}>
      {FIX_ALERT_INBOX.slice(0, 5).map((a) => (
        <div
          key={a.id}
          className={visual.surface3}
          style={{
            border: `1px solid ${a.state === "firing" ? "#5A2A2A" : "var(--cc-border)"}`,
            borderLeft: `3px solid ${
              a.severity === "high"
                ? "var(--danger)"
                : a.severity === "medium"
                  ? "var(--warn)"
                  : "var(--fg-faint)"
            }`,
          }}
        >
          <div className={visual.row}>
            <StatusBadge
              tone={
                a.state === "firing" ? "danger" : a.state === "acknowledged" ? "warn" : "success"
              }
              label={a.state.toUpperCase()}
              size="sm"
              filled
            />
            <span className={visual.caption}>
              {new Date(a.fired_at).toISOString().slice(11, 16)} UTC
            </span>
          </div>
          <div className={visual.label}>{a.subject}</div>
        </div>
      ))}
    </div>
  </Panel>
);
