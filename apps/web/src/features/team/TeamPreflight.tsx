import type { PreflightReportDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";

/**
 * 项目参考协议预检（WP-C）：协议名来自项目设置 reference_protocol，
 * 不再硬编码 demo 模板；未配置时诚实空态（引导到项目设置）。
 */
export function TeamPreflight({
  protocol,
  report,
  error,
  pending,
  onCheck,
}: {
  protocol: string | null;
  report: PreflightReportDto | null;
  error: string | null;
  pending: boolean;
  onCheck: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const unconfigured = protocol === null;
  return (
    <PanelSection
      title={
        zh
          ? "参考协议预检 · 保存绑定后刷新"
          : "Reference-protocol preflight · refreshed after saving"
      }
      extra={
        <button
          type="button"
          className="btn sm"
          disabled={pending || unconfigured}
          onClick={onCheck}
        >
          {zh ? "重新预检参考协议" : "Check reference protocol"}
        </button>
      }
    >
      <PreflightNotice protocol={protocol} zh={zh} />
      {pending ? (
        <LoadingState message={zh ? "后端正在预检…" : "Backend preflight in progress…"} />
      ) : unconfigured ? (
        <EmptyState message={zh ? "未配置参考协议" : "Reference protocol not configured"} />
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

function PreflightNotice({ protocol, zh }: { protocol: string | null; zh: boolean }) {
  const text =
    protocol === null
      ? zh
        ? "未配置项目参考协议（设置 → 工作区 → 参考协议）；配置后可对模板与当前绑定做只读预检。"
        : [
            "No project reference protocol configured (Settings → Workspace → ",
            "Reference protocol); once configured, a read-only preflight runs against ",
            "the template and current bindings.",
          ].join("")
      : [
          protocol,
          " · ",
          zh
            ? "仅对此模板及当前配置有效，不是选中运行的预检，不改写已冻结 Manifest。"
            : [
                "Applies only to this template and current configuration, not the ",
                "selected run or frozen manifests.",
              ].join(""),
        ].join("");
  return <p className={styles.notice}>{text}</p>;
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
