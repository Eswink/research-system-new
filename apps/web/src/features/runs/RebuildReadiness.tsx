import type { RebuildReadinessDto } from "../../api/types";
import { Chip } from "../../components/Chip";
import { PanelSection } from "../../components/PanelSection";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";

// 读面字段名 → 展示文案。映射只影响**展示**，不改 API 字段名（EC-06 的 `missing` 是
// 行字段名，对 API 消费者可读、对页面读者不友好）。未收录的名字原样展示，不猜语义。
const FIELD_LABELS: Record<string, { zh: string; en: string }> = {
  manifest_semantic_digest: { zh: "冻结语义摘要", en: "Frozen semantic digest" },
  protocol_body: { zh: "协议正文", en: "Protocol body" },
  frozen_manifest: { zh: "冻结的 Manifest", en: "Frozen manifest" },
};

function fieldLabel(name: string, zh: boolean): string {
  const entry = FIELD_LABELS[name];
  if (entry === undefined) return name;
  return `${zh ? entry.zh : entry.en}（${name}）`;
}

/** 三态各自的**结论**文案——刻意不预告重建结果（读面只回答输入齐不齐）。 */
function statusCopy(status: string, zh: boolean): string {
  if (status === "SELF_CONTAINED") {
    return zh
      ? "记录自足：重建所需输入都在库内"
      : "Self-contained: the inputs a rebuild needs are in the store";
  }
  if (status === "SOURCE_DEPENDENT") {
    return zh ? "依赖来源：缺下面点名的事实" : "Source-dependent: the facts below are missing";
  }
  if (status === "REFUSED") {
    return zh
      ? "读面拒绝给出结论（这不是「不可回填」的判定）"
      : "The read surface refuses to answer (not a verdict that backfill is impossible)";
  }
  return status;
}

function statusTone(status: string): "accent" | "warn" | "neutral" {
  if (status === "SELF_CONTAINED") return "accent";
  if (status === "SOURCE_DEPENDENT") return "warn";
  return "neutral";
}

export function RebuildReadiness({ rebuild }: { rebuild: RebuildReadinessDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <PanelSection
      title={zh ? "重建就绪（读面）" : "Rebuild readiness (read surface)"}
      extra={
        <Chip tone={statusTone(rebuild.status)}>
          <span data-testid="run-rebuild-status">{rebuild.status}</span>
        </Chip>
      }
    >
      <div data-testid="run-rebuild">
        <p className="muted">{statusCopy(rebuild.status, zh)}</p>
        {rebuild.missing.length > 0 && (
          <div data-testid="run-rebuild-missing">
            <KeyValueList
              fields={rebuild.missing.map((name) => ({
                label: zh ? "缺失事实" : "Missing fact",
                value: fieldLabel(name, zh),
              }))}
            />
          </div>
        )}
        <p className="muted" data-testid="run-rebuild-note">
          {zh
            ? "这是输入齐不齐的结论，不预告重建结果；重建能否通过仍要真跑一次。"
            : [
                "This answers whether inputs are complete; it does not predict the rebuild ",
                "result. Whether a rebuild passes still requires running one.",
              ].join("")}
        </p>
      </div>
    </PanelSection>
  );
}
