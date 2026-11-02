/**
 * 评审判词列表（GOAL-20261103-104 EC-03）。
 *
 * **它补的一格**：`GET /runs/{id}/reviews` 是后端的验收门读面（GOAL-035 EC-01），
 * `ReviewFindingDto` 早在 `types.ts` 里，但前端**没有任何消费者** —— 用户看不到
 * 「谁在哪个模型上判了什么」。
 *
 * **前端不做聚合**：`aggregate_panel` 是领域逻辑（平票 ⇒ advisory 为 `None`、
 * 无身份者不进票、单评审不聚合）。在 UI 里复刻它会漂移，而且会把「面板建议」冒充成
 * 「领域判定」—— 这两者在域里是**刻意分开**的。这里只逐条列原文。
 *
 * **归因要可见**：`reviewer_model` 为 `null` = 未声明该面。它**不等于**「同一个模型」，
 * 也**不等于**「独立」⇒ 显式写成「未声明」，不猜。
 */

import type { ReviewFindingDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import reviewStyles from "./ReviewPanelSection.module.css";

/** 判词极性 → 展示色调。闭集外的取值原样显示为中性（不猜语义）。 */
function verdictTone(verdict: string): "accent" | "warn" | "danger" | "neutral" {
  const normalized = verdict.toLowerCase();
  if (normalized === "pass" || normalized === "passed" || normalized === "approve") return "accent";
  if (normalized === "warn" || normalized === "advisory") return "warn";
  if (normalized === "fail" || normalized === "failed" || normalized === "reject") return "danger";
  return "neutral";
}

function ReviewRow({ finding, zh }: { finding: ReviewFindingDto; zh: boolean }) {
  return (
    <li className={reviewStyles.row} data-testid={`review-finding-${finding.id}`}>
      <div className={reviewStyles.head}>
        <Chip tone={verdictTone(finding.verdict)}>{finding.verdict}</Chip>
        <span className="mono">{finding.review_type}</span>
        <span className={reviewStyles.muted}>
          {zh ? "评审者" : "Reviewer"}: {finding.reviewed_by ?? (zh ? "未声明" : "undeclared")}
        </span>
        <span className={reviewStyles.muted} data-testid={`review-model-${finding.id}`}>
          {zh ? "评审模型" : "Reviewer model"}:{" "}
          {finding.reviewer_model ?? (zh ? "未声明（不等于同一模型）" : "undeclared (not the same model)")}
        </span>
        {finding.reviewed_at === null ? null : (
          <span className={reviewStyles.muted}>{finding.reviewed_at}</span>
        )}
      </div>
      {/* 判词是域函数逐字给出的：读面读原文，不在读取时重算。 */}
      <ul className={reviewStyles.findings}>
        {finding.findings.map((line) => (
          <li key={line} className="mono">
            {line}
          </li>
        ))}
      </ul>
    </li>
  );
}

export function ReviewPanelSection({
  findings,
  loading,
  error,
}: {
  findings: ReviewFindingDto[] | null;
  loading: boolean;
  error: string | null;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  if (loading) {
    return null;
  }
  if (error !== null) {
    // 读面拒绝/不可用要**说出来**，不能渲染成「没有判词」。
    return (
      <PanelSection title={zh ? "评审判词" : "Review verdicts"}>
        <p className={styles.notice} data-testid="review-panel-error">
          {zh ? `判词读面不可用：${error}` : `Review read surface unavailable: ${error}`}
        </p>
      </PanelSection>
    );
  }
  if (findings === null) {
    return null;
  }
  if (findings.length === 0) {
    return (
      <PanelSection title={zh ? "评审判词" : "Review verdicts"}>
        <p className={styles.notice} data-testid="review-panel-empty">
          {zh
            ? "这条运行还没有落库的评审判词（不是「评审通过」）。"
            : "No review verdict is recorded for this run (not the same as passing review)."}
        </p>
      </PanelSection>
    );
  }
  return (
    <PanelSection
      title={zh ? "评审判词" : "Review verdicts"}
      count={findings.length}
    >
      <ul className={reviewStyles.list} data-testid="review-panel">
        {findings.map((finding) => (
          <ReviewRow key={finding.id} finding={finding} zh={zh} />
        ))}
      </ul>
    </PanelSection>
  );
}
