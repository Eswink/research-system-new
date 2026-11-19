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

import type { PanelAdviceDto, ReviewFindingDto } from "../../api/types";
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

/** 票型 → `判词×票数`（键序稳定，空表说「无」）。
 *
 * **不写判词字面量**：`tests/architecture/typescript/production-boundaries.test.mjs`
 * 禁止 `apps/web/src/features` 出现验收判词词表 —— 前端不该自造判词词汇，
 * 只渲染后端发来的取值。本条注释此前写了一个词表里的字面量，被判据抓到。
 */
function votesText(votes: Record<string, number>, zh: boolean): string {
  const parts = Object.entries(votes).map(([verdict, count]) => `${verdict}×${String(count)}`);
  return parts.length === 0 ? (zh ? "无" : "none") : parts.join(" / ");
}

function adviceTone(advice: PanelAdviceDto): "accent" | "warn" | "danger" | "neutral" {
  if (advice.advisory === null) return "neutral";
  return verdictTone(advice.advisory);
}

function AdviceHead({ advice, zh }: { advice: PanelAdviceDto; zh: boolean }) {
  return (
    <div className={reviewStyles.head}>
      <span className="mono">{advice.phase_id}</span>
      <Chip tone={adviceTone(advice)}>
        {advice.advisory ?? (zh ? "无多数" : "no majority")}
      </Chip>
      <span className={reviewStyles.muted} data-testid={`panel-votes-${advice.phase_id}`}>
        {zh ? "票型" : "Votes"}: {votesText(advice.votes, zh)}
      </span>
      <span className={reviewStyles.muted}>
        {zh ? "可归因票" : "Voters"}: {advice.voters}
      </span>
      <span className={reviewStyles.muted} data-testid={`panel-independent-${advice.phase_id}`}>
        {zh ? "独立" : "Independent"}: {advice.independent ? (zh ? "是" : "yes") : zh ? "否" : "no"}
      </span>
    </div>
  );
}

function AdviceNotes({ advice, zh }: { advice: PanelAdviceDto; zh: boolean }) {
  return (
    <>
      {advice.dissent.length === 0 ? null : (
        <p className={reviewStyles.muted} data-testid={`panel-dissent-${advice.phase_id}`}>
          {zh ? "少数意见" : "Dissent"}: {advice.dissent.join("; ")}
        </p>
      )}
      <p className={reviewStyles.muted}>
        {[...advice.notes, ...advice.independence_notes].join("; ")}
      </p>
    </>
  );
}

/**
 * **面板建议**（GOAL-20261119-115 EC-05）：一负一过在这里读得出来。
 *
 * 它**不是**验收结论：硬门仍是后端 `REVIEW_SCORE >= 0.8` 与 `panel_rejection()`，
 * 两者一行未改。这一块只把已经落库的聚合读数显示出来。
 */
function PanelAdviceRows({ advices, zh }: { advices: PanelAdviceDto[]; zh: boolean }) {
  return (
    <ul className={reviewStyles.list} data-testid="panel-advice">
      {advices.map((advice) => (
        <li
          key={advice.phase_id}
          className={reviewStyles.row}
          data-testid={`panel-advice-${advice.phase_id}`}
        >
          <AdviceHead advice={advice} zh={zh} />
          <AdviceNotes advice={advice} zh={zh} />
        </li>
      ))}
    </ul>
  );
}

/** 空态与错误态（两种都必须说出来；抽出来守 50 行函数门）。 */
function ReviewNotice({ zh, testId, text }: { zh: boolean; testId: string; text: string | null }) {
  const message =
    text === null
      ? zh
        ? "这条运行还没有落库的评审判词（不是「评审通过」）。"
        : "No review verdict is recorded for this run (not the same as passing review)."
      : zh
        ? `判词读面不可用：${text}`
        : `Review read surface unavailable: ${text}`;
  return (
    <PanelSection title={zh ? "评审判词" : "Review verdicts"}>
      <p className={styles.notice} data-testid={testId}>
        {message}
      </p>
    </PanelSection>
  );
}

export function ReviewPanelSection({
  findings,
  advice = null,
  loading,
  error,
}: {
  findings: ReviewFindingDto[] | null;
  advice?: PanelAdviceDto[] | null;
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
    return <ReviewNotice zh={zh} testId="review-panel-error" text={error} />;
  }
  if (findings === null) {
    return null;
  }
  if (findings.length === 0) {
    return <ReviewNotice zh={zh} testId="review-panel-empty" text={null} />;
  }
  return (
    <PanelSection
      title={zh ? "评审判词" : "Review verdicts"}
      count={findings.length}
    >
      {advice === null || advice.length === 0 ? null : (
        <PanelAdviceRows advices={advice} zh={zh} />
      )}
      <ul className={reviewStyles.list} data-testid="review-panel">
        {findings.map((finding) => (
          <ReviewRow key={finding.id} finding={finding} zh={zh} />
        ))}
      </ul>
    </PanelSection>
  );
}
