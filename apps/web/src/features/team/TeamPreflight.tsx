import type { PreflightReportDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

export const TEAM_REFERENCE_PROTOCOL = "console_demo_research_v1.yaml";

export function TeamPreflight({
  report,
  error,
  pending,
  onCheck,
}: {
  report: PreflightReportDto | null;
  error: string | null;
  pending: boolean;
  onCheck: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <PanelSection
      title={
        zh
          ? "参考协议预检 · 保存绑定后刷新"
          : "Reference-protocol preflight · refreshed after saving"
      }
      extra={
        <button type="button" className="btn sm" disabled={pending} onClick={onCheck}>
          {zh ? "重新预检参考协议" : "Check reference protocol"}
        </button>
      }
    >
      <p className={styles.notice}>
        {TEAM_REFERENCE_PROTOCOL} ·{" "}
        {zh
          ? "仅对此模板及当前配置有效，不是选中运行的预检，不改写已冻结 Manifest。"
          : [
              "Applies only to this template and current configuration, not the ",
              "selected run or frozen manifests.",
            ].join("")}
      </p>
      {pending ? (
        <LoadingState message={zh ? "后端正在预检…" : "Backend preflight in progress…"} />
      ) : error !== null ? (
        <ErrorState message={error} />
      ) : report === null ? (
        <EmptyState message={zh ? "尚未预检" : "Not checked"} />
      ) : (
        <PreflightFindings report={report} />
      )}
    </PanelSection>
  );
}

function PreflightFindings({ report }: { report: PreflightReportDto }) {
  // Tone derives from backend-owned findings presence, never from a locally
  // invented verdict string; the backend status itself is echoed verbatim.
  const tone = report.findings.length > 0 ? "warn" : "success";
  return (
    <div data-testid="team-preflight-findings">
      <Chip tone={tone}>
        <span data-preflight-status={report.status}>{report.status}</span>
      </Chip>
      {report.findings.length === 0 ? (
        <p data-testid="team-preflight-ok">
          <span data-preflight-status={report.status}>{report.status}</span> · 0 findings
        </p>
      ) : (
        <ul className={styles.list}>
          {report.findings.map((finding, index) => (
            <li key={`${finding.code}:${String(index)}`} className={styles.notice}>
              <strong>
                {finding.severity} · {finding.code}
              </strong>
              <p>{finding.message}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
