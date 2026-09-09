import type * as FixtureTypes from "../../fixtureTypes";
import { Icon } from "../Icon";
import visual from "../IntegrationsScreen.module.css";
import { IntegrationsStatConnected2 } from "./IntegrationsStatConnected2";

interface IntegrationsStatConnectedProps {
  filtered: FixtureTypes.Integration[];
  t: (key: string, fallback?: string) => string;
}

export function IntegrationsStatConnected({ filtered, t }: IntegrationsStatConnectedProps) {
  return (
    <div className={visual.grid}>
      {filtered.map((int) => (
        <div key={int.id} className={`panel ${visual.panel ?? ""}`}>
          <div className={visual.row}>
            <div className={visual.row2}>{int.name.slice(0, 2).toUpperCase()}</div>
            <div className={visual.surface}>
              <div className={visual.label}>{int.name}</div>
              <div className={`mono ${visual.caption ?? ""}`}>{int.category.toUpperCase()}</div>
            </div>
          </div>
          <IntegrationsStatConnected2 {...{ int, t }} />
          {int.status === "connected" && Object.keys(int.meta).length > 0 && (
            <div className={visual.caption2}>
              {Object.entries(int.meta)
                .slice(0, 2)
                .map(([k, v]) => (
                  <div key={k}>
                    <span className={visual.surface2}>{k}:</span> {v}
                  </div>
                ))}
            </div>
          )}
          {int.issue && <div className={visual.caption3}>{int.issue}</div>}
          {int.disconnect_reason && <div className={visual.caption4}>{int.disconnect_reason}</div>}
          <div className={visual.row4}>
            {int.status === "connected" && (
              <button className="btn sm ghost">{t("act.configure")}</button>
            )}
            {int.status === "available" && (
              <button className={`btn sm primary ${visual.action ?? ""}`}>
                <Icon name="plus" size={10} /> {t("act.connect")}
              </button>
            )}
            {int.status === "disconnected" && (
              <button className={`btn sm ${visual.action2 ?? ""}`}>
                <Icon name="spin" size={10} /> {t("act.reconnect")}
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
