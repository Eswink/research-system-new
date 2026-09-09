import FIX_AGENTS from "../data/agents.json";
import FIX_ALERT_INBOX from "../data/alert-inbox.json";
import FIX_PROJECTS from "../data/projects.json";
import visual from "./CommandCenter.module.css";
import { FooterBar } from "./FooterBar";
import { PanelActiveRuns } from "./PanelActiveRuns";
import { PanelAlertsFeed } from "./PanelAlertsFeed";
import { PanelClaimsFlow } from "./PanelClaimsFlow";
import { PanelCostBurn } from "./PanelCostBurn";
import { PanelEventTicker } from "./PanelEventTicker";
import { PanelExperimentPipeline } from "./PanelExperimentPipeline";
import { PanelHealth } from "./PanelHealth";
import { PanelModelActivity } from "./PanelModelActivity";
import { PanelWorldMap } from "./PanelWorldMap";
import { StatBlock } from "./StatBlock";

/** Reference: Command Center.html; every metric is a fixed example. */
export const CommandCenter = () => {
  const clock = new Date("2026-08-27T14:42:11Z");

  // ─── Header data ───
  const runningProjects = FIX_PROJECTS.filter((p) => p.status === "RUNNING").length;
  const totalSpent = FIX_PROJECTS.reduce((a, p) => a + p.spent_minor, 0);
  const totalBudget = FIX_PROJECTS.reduce((a, p) => a + p.budget_minor, 0);
  const firingAlerts = FIX_ALERT_INBOX.filter((a) => a.state === "firing").length;

  return (
    <div className={visual.column}>
      {/* ── TOP MASTHEAD ── */}
      <CommandCenterSection
        {...{ runningProjects, totalSpent, totalBudget, firingAlerts, clock }}
      />

      {/* ── MAIN GRID: 12 columns × 3 rows ── */}
      <div className={visual.grid}>
        {/* ROW 1 */}
        <PanelActiveRuns />
        <PanelWorldMap />
        <PanelHealth />

        {/* ROW 2 */}
        <PanelClaimsFlow />
        <PanelCostBurn />
        <PanelAlertsFeed />

        {/* ROW 3 */}
        <PanelExperimentPipeline />
        <PanelModelActivity />
        <PanelEventTicker />
      </div>

      {/* ── FOOTER TICKER ── */}
      <FooterBar />
    </div>
  );
};

interface CommandCenterSectionProps {
  runningProjects: number;
  totalSpent: number;
  totalBudget: number;
  firingAlerts: number;
  clock: Date;
}

function CommandCenterSection({
  runningProjects,
  totalSpent,
  totalBudget,
  firingAlerts,
  clock,
}: CommandCenterSectionProps) {
  return (
    <div className={visual.row}>
      <div className={visual.row2}>
        <div className={visual.row3}>◇</div>
        <div>
          <div className={visual.label}>Research OS</div>
          <div className={visual.label2}>COMMAND CENTER · MISSION CONTROL</div>
        </div>
      </div>

      <div className={visual.indicator} />

      <CommandCenterSection2 {...{ runningProjects, totalSpent, totalBudget, firingAlerts }} />

      <div className={visual.row5}>
        <div className={visual.surface}>
          <div className={visual.label3}>{clock.toISOString().slice(11, 19)}</div>
          <div className={visual.label4}>UTC · {clock.toISOString().slice(0, 10)}</div>
        </div>
        <div className={visual.row6}>
          <div className={`pulse-dot ${visual.indicator2 ?? ""}`} />
          EXAMPLE · NOT LIVE
        </div>
      </div>
    </div>
  );
}

interface CommandCenterSection2Props {
  runningProjects: number;
  totalSpent: number;
  totalBudget: number;
  firingAlerts: number;
}

function CommandCenterSection2({
  runningProjects,
  totalSpent,
  totalBudget,
  firingAlerts,
}: CommandCenterSection2Props) {
  return (
    <div className={visual.row4}>
      <StatBlock
        label="ACTIVE PROJECTS"
        value={runningProjects}
        sub={`of ${String(FIX_PROJECTS.length)}`}
      />
      <StatBlock label="RUNNING AGENTS" value={FIX_AGENTS.length} sub="across all runs" />
      <StatBlock
        label="SPEND · 30D"
        value={`$${(totalSpent / 100000).toFixed(0)}`}
        sub={`of $${(totalBudget / 100000).toFixed(0)} cap`}
        color="var(--warn)"
      />
      <StatBlock
        label="FIRING"
        value={firingAlerts}
        sub="alerts unacked"
        color={firingAlerts > 0 ? "var(--danger)" : "var(--success)"}
      />
    </div>
  );
}
