import FIX_ALERT_INBOX from "../../data/alert-inbox.json";
import visual from "../AlertsScreen.module.css";
import { StatusBadge } from "../StatusBadge";
import { AlertsLabel } from "./AlertsLabel";

export function AlertsSection() {
  return (
    <div className={visual.surface2}>
      {FIX_ALERT_INBOX.map((a) => (
        <div key={a.id} className={`row ${visual.surface3 ?? ""}`}>
          <AlertsLabel {...{ a }} />
          <span>
            <StatusBadge
              tone={a.severity === "high" ? "danger" : a.severity === "medium" ? "warn" : "neutral"}
              label={a.severity.toUpperCase()}
              icon={
                a.severity === "high"
                  ? "warn-tri"
                  : a.severity === "medium"
                    ? "diamond"
                    : "circle-o"
              }
              filled
            />
          </span>
          <span>
            <StatusBadge
              tone={
                a.state === "firing" ? "danger" : a.state === "acknowledged" ? "warn" : "success"
              }
              label={a.state.toUpperCase()}
              icon={
                a.state === "firing" ? "warn-tri" : a.state === "acknowledged" ? "clock" : "check"
              }
            />
          </span>
          <span className={visual.label}>{a.subject}</span>
          <span className={`mono ${visual.caption ?? ""}`}>{a.rule_id}</span>
          <span className={`mono ${visual.caption2 ?? ""}`}>
            {new Date(a.fired_at).toISOString().replace("T", " ").slice(5, 16)}
          </span>
          <span className={visual.caption3}>{a.ack_by ? a.ack_by.split("@")[0] : "—"}</span>
        </div>
      ))}
    </div>
  );
}
