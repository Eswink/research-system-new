import { useState } from "react";
import { api } from "../../api/client";
import { PanelSection } from "../../components/PanelSection";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { TrendView } from "./TrendView";

export function EvaluationQuery() {
  const { language } = useI18n();
  const zh = language === "zh";
  const [draft, setDraft] = useState("");
  const [dataset, setDataset] = useState("");
  const trend = useResource(`evaluation:${dataset}`, () => api.evaluationsTrend(dataset, [], 30));
  return (
    <PanelSection
      title={zh ? "评测与回归 · 独立来源" : "Evaluation and regression · independent source"}
    >
      <form
        className={styles.query}
        onSubmit={(event) => {
          event.preventDefault();
          const value = draft.trim();
          if (value === dataset) trend.reload();
          else setDataset(value);
        }}
      >
        <label className={styles.queryLabel}>
          {zh ? "数据集 ID（可选）" : "Dataset ID (optional)"}
          <input
            className="input mono"
            value={draft}
            onChange={(event) => {
              setDraft(event.target.value);
            }}
          />
        </label>
        <button className="btn" type="submit" disabled={trend.phase === "loading"}>
          {zh ? "读取评测趋势" : "Load Evaluation Trend"}
        </button>
      </form>
      <p className={styles.notice}>
        {zh
          ? "最多读取近期 30 条，按服务端可比性分段。不把不同数据集、门禁或系统版本拼成单一趋势。"
          : [
              "Up to 30 recent reports, segmented by server comparability. Different ",
              "datasets, gates and system versions are not joined into one trend.",
            ].join("")}
      </p>
      <ResourceBoundary state={trend}>
        {trend.data !== null && <TrendView trend={trend.data} />}
      </ResourceBoundary>
    </PanelSection>
  );
}
