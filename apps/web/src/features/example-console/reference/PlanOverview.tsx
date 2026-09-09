import FIX_AGENTS from "../data/agents.json";
import FIX_CLAIMS from "../data/claims.json";
import FIX_PREFLIGHT from "../data/preflight.json";
import FIX_RUN from "../data/run.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { DigestText } from "./DigestText";
import { Icon } from "./Icon";
import { ObjectiveRow } from "./ObjectiveRow";
import visual from "./PlanOverview.module.css";
import { PreflightBadge } from "./PreflightBadge";

/** Reference: components/AppShell.jsx; EXAMPLE ONLY. */
export const PlanOverview = () => {
  const { t } = useI18n();
  const preflightWarns = FIX_PREFLIGHT.WARN.findings.filter((f) => f.severity === "warning").length;
  return (
    <div className={visual.surface}>
      <PlanOverviewSection {...{ t, preflightWarns }} />
    </div>
  );
};

interface PlanOverviewSectionProps {
  t: (key: string, fallback?: string) => string;
  preflightWarns: number;
}

function PlanOverviewSection({ t, preflightWarns }: PlanOverviewSectionProps) {
  return (
    <div className={visual.column}>
      <PlanOverviewSection3 {...{ t }} />

      <PlanOverviewSection2 {...{ t, preflightWarns }} />

      <div className={`panel ${visual.panel4 ?? ""}`}>
        <div className={visual.caption5}>{t("ov.objectives")}</div>
        <div className={visual.column2}>
          <ObjectiveRow id="obj_hall_rate" statement={t("ov.obj1")} status="ongoing" />
          <ObjectiveRow id="obj_var_ranking" statement={t("ov.obj2")} status="pending" />
        </div>
      </div>

      <div className={`panel ${visual.panel5 ?? ""}`}>
        <div className={visual.caption6}>{t("ov.quickJump")}</div>
        <div className={visual.grid2}>
          {(
            [
              ["timeline", t("ov.qj.timeline"), "graph", t("ov.qj.timelineSub")],
              ["approvals", t("ov.qj.approvals"), "shield", t("ov.qj.approvalsSub")],
              ["claims", t("ov.qj.claims"), "diamond", t("ov.qj.claimsSub")],
              ["budget", t("ov.qj.budget"), "warn-tri", t("ov.qj.budgetSub")],
            ] as const
          ).map(([tid, label, icn, sub]) => (
            <div key={tid} className={visual.surface4}>
              <div className={visual.row4}>
                <Icon name={icn} size={11} className={visual.surface5} />
                <span className={visual.label11}>{label}</span>
              </div>
              <div className={visual.label12}>{sub}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface PlanOverviewSection2Props {
  t: (key: string, fallback?: string) => string;
  preflightWarns: number;
}

interface PlanOverviewSection3Props {
  t: (key: string, fallback?: string) => string;
}

function PlanOverviewSection3({ t }: PlanOverviewSection3Props) {
  return (
    <div>
      <div className={visual.caption}>{t("ov.kicker")}</div>
      <div className={visual.label}>{t("ov.title")}</div>
      <div className={visual.row}>
        <DigestText value={FIX_RUN.manifest_digest} label="manifest:" length={12} />
        <span>·</span>
        <span>
          {t("ov.objectives")}: <span className={visual.surface2}>2</span>
        </span>
        <span>·</span>
        <span>
          {t("ov.team")}: <span className="mono">STANDARD</span> (8 {t("ov.roles")} ·{" "}
          {FIX_AGENTS.length} {t("ov.agents")})
        </span>
        <span>·</span>
        <span>
          {t("ov.autonomy")}:{" "}
          <span className={`mono ${visual.surface3 ?? ""}`}>GUARDED_AUTONOMOUS</span>
        </span>
      </div>
    </div>
  );
}

function PlanOverviewSection2({ t, preflightWarns }: PlanOverviewSection2Props) {
  return (
    <div className={visual.grid}>
      <div className={`panel ${visual.panel ?? ""}`}>
        <div className={visual.caption2}>{t("ov.preflight")}</div>
        <PreflightBadge status="WARN" />
        <div className={visual.label2}>
          {preflightWarns} {t("ov.warnings")}
        </div>
      </div>
      <div className={`panel ${visual.panel2 ?? ""}`}>
        <div className={visual.caption3}>{t("ov.runProgress")}</div>
        <div className={visual.row2}>
          <span className={visual.label3}>{FIX_RUN.progress.tasks_done}</span>
          <span className={visual.label4}>
            / {FIX_RUN.progress.tasks_total} {t("ov.tasksDone")}
          </span>
        </div>
        <div className={visual.indicator}>
          <div
            className={visual.indicator2}
            style={{
              width: `${String(
                (FIX_RUN.progress.tasks_done / FIX_RUN.progress.tasks_total) * 100,
              )}%`,
            }}
          />
        </div>
      </div>
      <PlanOverviewSection4 {...{ t }} />
    </div>
  );
}

interface PlanOverviewSection4Props {
  t: (key: string, fallback?: string) => string;
}

function PlanOverviewSection4({ t }: PlanOverviewSection4Props) {
  return (
    <div className={`panel ${visual.panel3 ?? ""}`}>
      <div className={visual.caption4}>{t("ov.claims")}</div>
      <div className={visual.row3}>
        <div>
          <span className={visual.label5}>
            {FIX_CLAIMS.filter((c) => c.status === "VERIFIED").length}
          </span>{" "}
          <span className={visual.label6}>{t("ov.verified")}</span>
        </div>
        <div>
          <span className={visual.label7}>
            {FIX_CLAIMS.filter((c) => c.status === "DISPUTED").length}
          </span>{" "}
          <span className={visual.label8}>{t("ov.disputed")}</span>
        </div>
        <div>
          <span className={visual.label9}>
            {FIX_CLAIMS.filter((c) => c.status === "PROPOSED").length}
          </span>{" "}
          <span className={visual.label10}>{t("ov.proposed")}</span>
        </div>
      </div>
    </div>
  );
}
