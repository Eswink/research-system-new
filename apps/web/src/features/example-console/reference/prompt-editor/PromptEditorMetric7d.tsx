import type * as FixtureTypes from "../../fixtureTypes";
import { Icon } from "../Icon";
import { MetricCard } from "../MetricCard";
import visual from "../PromptEditor.module.css";
import { TextArea } from "../TextArea";
import { PromptEditorMetricErr } from "./PromptEditorMetricErr";
import { PromptEditorMetricLat } from "./PromptEditorMetricLat";
import { PromptEditorSection2 } from "./PromptEditorSection2";

interface PromptEditorMetric7dProps {
  tab: string;
  t: (key: string, fallback?: string) => string;
  prompt: FixtureTypes.Prompt;
}

export function PromptEditorMetric7d({ tab, t, prompt }: PromptEditorMetric7dProps) {
  return (
    <div className={visual.surface3}>
      {tab === "template" && <PromptTemplateTab {...{ t, prompt }} />}
      {tab === "variables" && <PromptVariablesTab {...{ t, prompt }} />}
      {tab === "history" && <PromptHistoryTab {...{ t, prompt }} />}
      {tab === "metrics" && <PromptMetricsTab {...{ t, prompt }} />}
    </div>
  );
}

function PromptTemplateTab({ t, prompt }: Omit<PromptEditorMetric7dProps, "tab">) {
  return (
    <div>
      <div className={visual.row5}>
        <div className={visual.caption2}>
          {t("pr.tabTemplate")} · {prompt.latest_version}
        </div>
        <div className={visual.caption3}>
          {prompt.template.split("\n").length} {t("pr.lines")} · {prompt.template.length}{" "}
          {t("pr.chars")}
        </div>
      </div>
      <pre className={visual.label2}>
        {prompt.template.split(/(\{[^}]+\})/g).map((part, index) =>
          part.startsWith("{") ? (
            <span key={index} className={visual.surface4}>
              {part}
            </span>
          ) : (
            <span key={index}>{part}</span>
          ),
        )}
      </pre>
      <div className={visual.caption4}>
        <span className={visual.surface5}>{t("pr.variables")}</span>{" "}
        {prompt.variables.map((variable) => (
          <span key={variable} className={`chip ${visual.caption5 ?? ""}`}>
            {"{" + variable + "}"}
          </span>
        ))}
      </div>
    </div>
  );
}

function PromptVariablesTab({ t, prompt }: Omit<PromptEditorMetric7dProps, "tab">) {
  return (
    <div className={visual.column}>
      {prompt.variables.map((variable) => (
        <div key={variable} className={visual.surface6}>
          <div className={visual.row6}>
            <span className={`mono ${visual.label3 ?? ""}`}>{"{" + variable + "}"}</span>
            <span className={`chip ${visual.caption6 ?? ""}`}>{t("pr.varStrReq")}</span>
          </div>
          <TextArea
            placeholder={t("pr.varExample").replace("{v}", "{" + variable + "}")}
            rows={3}
            mono
          />
        </div>
      ))}
    </div>
  );
}

function PromptHistoryTab({ t, prompt }: Omit<PromptEditorMetric7dProps, "tab">) {
  return (
    <div className={visual.column2}>
      {Array.from({ length: prompt.versions }, (_, index) => (
        <PromptHistoryRow key={prompt.versions - index} {...{ t, prompt, index }} />
      ))}
    </div>
  );
}

function PromptHistoryRow({
  t,
  prompt,
  index,
}: Omit<PromptEditorMetric7dProps, "tab"> & { index: number }) {
  const version = prompt.versions - index;
  const isLatest = index === 0;
  return (
    <div
      className={visual.row7}
      style={{
        background: isLatest ? "var(--accent-dim)" : "var(--bg-raised)",
        border: `1px solid ${isLatest ? "var(--accent-line)" : "var(--border)"}`,
      }}
    >
      <span
        className={`mono ${visual.label4 ?? ""}`}
        style={{ color: isLatest ? "var(--accent)" : "var(--fg-muted)" }}
      >
        v{version}
      </span>
      <PromptEditorSection2 i={index} v={version} prompt={prompt} />
      {isLatest && <span className={`chip ${visual.caption8 ?? ""}`}>{t("pr.verLatest")}</span>}
      <button className="btn sm ghost">
        <Icon name="external" size={10} />
      </button>
    </div>
  );
}

function PromptMetricsTab({ t, prompt }: Omit<PromptEditorMetric7dProps, "tab">) {
  const trendClass = `mono ${visual.surface8 ?? ""}`;
  return (
    <div className={visual.grid}>
      <MetricCard
        label={t("pr.metric7d")}
        value={prompt.usage_7d.toLocaleString()}
        sub={
          <span>
            {t("pr.metric7dSub")} <span className={trendClass}>+12.4%</span> WoW
          </span>
        }
        spark={[3, 4, 3, 5, 7, 6, 8]}
      />
      <PromptEditorMetricLat {...{ t, prompt }} />
      <PromptEditorMetricErr {...{ t }} />
    </div>
  );
}
