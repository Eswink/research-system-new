import * as React from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import { DigestText } from "../DigestText";
import { Icon } from "../Icon";
import visual from "../RunDiffView.module.css";
import { RunStateBadge } from "../RunStateBadge";
import { fmtDuration } from "../fmtDuration";

interface RunDiffViewSectionProps {
  a: FixtureTypes.Run;
  b: FixtureTypes.Run;
  t: (key: string, fallback?: string) => string;
}

export function RunDiffViewSection({ a, b, t }: RunDiffViewSectionProps) {
  return (
    <div className={visual.grid}>
      {[a, b].map((r, i) => (
        <React.Fragment key={r.id}>
          {i === 1 && (
            <div className={visual.row}>
              <div className={visual.surface}>
                <Icon name="chevron-r" size={14} className={visual.surface2} />
              </div>
            </div>
          )}
          <div className={`panel ${visual.panel ?? ""}`}>
            <div className={visual.caption}>{i === 0 ? t("rh.runA") : t("rh.runB")}</div>
            <div className={visual.row2}>
              <span className={visual.label}>{r.label}</span>
              <RunStateBadge state={r.state} />
            </div>
            <DigestText value={r.id} length={20} prefix={false} />
            <div className={visual.grid2}>
              <div>
                <div className={visual.caption2}>{t("rh.duration")}</div>
                <div className={visual.surface3}>{fmtDuration(r.duration_s)}</div>
              </div>
              <div>
                <div className={visual.caption3}>{t("rh.tasks")}</div>
                <div className={visual.surface4}>
                  {r.tasks_done}/{r.tasks_total}
                </div>
              </div>
              <div>
                <div className={visual.caption4}>{t("rh.spent")}</div>
                <div className={visual.surface5}>${(r.spent_minor / 100000).toFixed(2)}</div>
              </div>
            </div>
          </div>
        </React.Fragment>
      ))}
    </div>
  );
}
