import { type Dispatch, type SetStateAction } from "react";
import FIX_ALERT_INBOX from "../../data/alert-inbox.json";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../AlertsScreen.module.css";
import { MetricCard } from "../MetricCard";
import { AlertsNew } from "./AlertsNew";
import { AlertsSection } from "./AlertsSection";
import { AlertsSection2 } from "./AlertsSection2";
import { AlertsSection3 } from "./AlertsSection3";
import { AlertsTitle } from "./AlertsTitle";

interface AlertsMFiringProps {
  t: (key: string, fallback?: string) => string;
  tab: string;
  setTab: Dispatch<SetStateAction<string>>;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
  rules: FixtureTypes.AlertRule[];
  setRules: Dispatch<SetStateAction<FixtureTypes.AlertRule[]>>;
  drawer: { mode?: string } | null;
}

const ALERT_CHANNELS = [
  { name: "Slack · #research-ops", type: "chat", status: "healthy", stats: "12 alerts / 24h" },
  { name: "Slack · #platform", type: "chat", status: "healthy", stats: "3 alerts / 24h" },
  {
    name: "PagerDuty · oncall-a",
    type: "pager",
    status: "degraded",
    stats: "on-call not set for weekends",
  },
  { name: "Email · pi@research.io", type: "email", status: "healthy", stats: "1 alert / 24h" },
  { name: "Webhook · audit-bus", type: "webhook", status: "healthy", stats: "62 events / 24h" },
];

export function AlertsMFiring({
  t,
  tab,
  setTab,
  setDrawer,
  rules,
  setRules,
  drawer,
}: AlertsMFiringProps) {
  return (
    <div className={visual.column}>
      <AlertsTitle {...{ t, tab, setTab, setDrawer }} />
      {tab === "inbox" && <AlertsInbox {...{ t, rules }} />}
      {tab === "rules" && <AlertsRules {...{ t, rules, setRules }} />}
      {tab === "channels" && <AlertsChannels />}

      <AlertsNew {...{ drawer, setDrawer, t }} />
    </div>
  );
}

function AlertsInbox({ t, rules }: Pick<AlertsMFiringProps, "t" | "rules">) {
  return (
    <>
      <div className={visual.grid}>
        <MetricCard
          label={t("al.mFiring")}
          value={FIX_ALERT_INBOX.filter((a) => a.state === "firing").length}
          sub={<span>{t("al.mFiringSub")}</span>}
        />
        <MetricCard
          label={t("al.mAcked")}
          value={FIX_ALERT_INBOX.filter((a) => a.state === "acknowledged").length}
          sub={<span>{t("al.mAckedSub")}</span>}
        />
        <MetricCard
          label={t("al.mResolved")}
          value={FIX_ALERT_INBOX.filter((a) => a.state === "resolved").length}
          sub={<span>{t("al.mResolvedSub")}</span>}
        />
        <MetricCard
          label={t("al.mRules")}
          value={rules.filter((r) => r.enabled).length}
          sub={<span>{t("al.mRulesSub").replace("{n}", String(rules.length))}</span>}
        />
      </div>
      <div className={`panel ${visual.panel ?? ""}`}>
        <div className={`row head ${visual.surface ?? ""}`}>
          <span></span>
          <span>{t("lbl.severity")}</span>
          <span>{t("lbl.state")}</span>
          <span>{t("lbl.subject")}</span>
          <span>{t("lbl.rule")}</span>
          <span>{t("lbl.firedAt")}</span>
          <span>{t("lbl.ackBy")}</span>
        </div>
        <AlertsSection {...{}} />
      </div>
    </>
  );
}

function AlertsRules({ t, rules, setRules }: Pick<AlertsMFiringProps, "t" | "rules" | "setRules">) {
  return (
    <div className={`panel ${visual.panel2 ?? ""}`}>
      <div className={`row head ${visual.surface4 ?? ""}`}>
        <span>{t("al.colOn")}</span>
        <span>{t("lbl.rule")}</span>
        <span>{t("lbl.severity")}</span>
        <span>{t("lbl.scope")}</span>
        <span>{t("lbl.channels")}</span>
        <span>{t("lbl.suppress")}</span>
        <span>7d</span>
      </div>
      <AlertsSection2 {...{ rules, setRules, t }} />
    </div>
  );
}

function AlertsChannels() {
  return (
    <div className={visual.grid2}>
      {ALERT_CHANNELS.map((c) => (
        <div key={c.name} className={`panel ${visual.panel3 ?? ""}`}>
          <AlertsSection3 {...{ c }} />
          <div className={visual.label4}>{c.stats}</div>
        </div>
      ))}
    </div>
  );
}
