import type { TrendPointDto, TrendSegmentDto, TrendViewDto } from "../../api/types";
import { BarSeries } from "../../components/charts/BarSeries";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";
import visual from "./TrendView.module.css";

export function TrendView({ trend }: { trend: TrendViewDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <div className={styles.page} data-testid="trend-view">
      <TrendNotices trend={trend} />
      {trend.segments.length === 0 && trend.missing.length === 0 && (
        <EmptyState message={zh ? "尚未存储评测报告" : "No evaluations stored"} />
      )}
      {trend.segments.map((segment, index) => (
        <div key={index} data-testid={`trend-segment-${String(index)}`}>
          <PanelSection
            title={`${zh ? "可比较分段" : "Comparable segment"} ${String(index + 1)}`}
            count={segment.points.length}
          >
            <SegmentChart segment={segment} />
            <div className={styles.cards}>
              {segment.points.map((point) => (
                <TrendPoint key={point.report_digest} point={point} />
              ))}
            </div>
            <RegressionMarkers segment={segment} />
          </PanelSection>
        </div>
      ))}
      {trend.missing.length > 0 && (
        <PanelSection title={zh ? "缺失报告" : "Missing reports"}>
          <div className={styles.cards}>
            {trend.missing.map((point) => (
              <TrendPoint key={point.report_digest} point={point} />
            ))}
          </div>
        </PanelSection>
      )}
    </div>
  );
}

function TrendNotices({ trend }: { trend: TrendViewDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <>
      {trend.truncated && (
        <p className={styles.notice} data-testid="trend-truncated">
          {zh
            ? "仅展示有界的近期窗口，不代表完整历史。"
            : "showing a bounded recent window, not the complete history"}
        </p>
      )}
      {trend.missing.length > 0 && (
        <p className={styles.notice} data-testid="trend-missing">
          {zh ? "缺失评测：" : "Missing evaluations: "}
          {trend.missing.map((point) => point.report_digest).join(", ")}
        </p>
      )}
      {trend.divergences.length > 0 && (
        <div data-testid="trend-divergences">
          {trend.divergences.map((divergence, index) => (
            <p key={index} className={styles.notice}>
              <strong>{divergence.verdict}</strong> · {divergence.reason}
            </p>
          ))}
        </div>
      )}
    </>
  );
}

function SegmentChart({ segment }: { segment: TrendSegmentDto }) {
  const { language } = useI18n();
  const known = segment.points.filter((point) => !point.missing && point.integrity_error === null);
  if (known.length === 0) return null;
  return (
    <figure className={visual.figure}>
      <BarSeries
        width={640}
        height={160}
        data={known.map((point) => ({
          label: point.report_digest.slice(-6),
          values: [point.pass_count, point.fail_count, point.infra_error_count],
        }))}
        series={[
          { key: "pass", color: "var(--success)" },
          { key: "fail", color: "var(--danger)" },
          { key: "infra", color: "var(--unknown)" },
        ]}
      />
      <figcaption>
        {language === "zh"
          ? "每报告：通过 / 失败 / 基础设施错误；缺失或完整性异常报告不绘制为零。"
          : [
              "Per report: pass / fail / infrastructure error. Missing or ",
              "integrity-failed reports are not plotted as zero.",
            ].join("")}
      </figcaption>
    </figure>
  );
}

function TrendPoint({ point }: { point: TrendPointDto }) {
  return (
    <article className={styles.card}>
      <div className={styles.cardHead}>
        <span className="mono">{point.report_digest}</span>
        <Chip tone={point.missing ? "unknown" : "neutral"}>{point.verdict}</Chip>
      </div>
      <KeyValueList
        fields={[
          { label: "Run", value: point.run_id ?? "—" },
          { label: "Recorded", value: point.recorded_at ?? "UNKNOWN" },
          { label: "Dataset", value: point.dataset_digest ?? "UNKNOWN" },
          { label: "Gate config", value: point.gate_config_digest ?? "UNKNOWN" },
          { label: "System", value: point.system_version ?? "UNKNOWN" },
        ]}
      />
      <PointCounts point={point} />
      {point.integrity_error !== null && (
        <p className={styles.notice}>Integrity: {point.integrity_error}</p>
      )}
    </article>
  );
}

function PointCounts({ point }: { point: TrendPointDto }) {
  const { language } = useI18n();
  if (point.missing || point.integrity_error !== null)
    return (
      <p className={styles.notice}>
        {language === "zh"
          ? "报告缺失或完整性异常，不将计数呈现为零。"
          : "Missing or integrity-failed report; counts are not rendered as zero."}
      </p>
    );
  return (
    <p>
      pass {point.pass_count} · fail {point.fail_count} · infra {point.infra_error_count}
      {" · "}reviewer failures {point.reviewer_failure_count}
    </p>
  );
}

function RegressionMarkers({ segment }: { segment: TrendSegmentDto }) {
  return (
    <ul className={styles.list}>
      {segment.comparisons.map((marker, index) => (
        <li key={index} className={styles.notice}>
          <strong>{marker.verdict}</strong>
          <p className="mono">
            {marker.baseline_digest} → {marker.candidate_digest}
          </p>
          <p>Regressed: {marker.newly_regressed.join(", ") || "—"}</p>
          <p>Fixed: {marker.newly_fixed.join(", ") || "—"}</p>
        </li>
      ))}
    </ul>
  );
}
