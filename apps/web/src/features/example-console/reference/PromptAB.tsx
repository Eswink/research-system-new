import FIX_PROMPT_AB from "../data/prompt-ab.json";
import type * as E from "../exampleTypes";
import type * as FixtureTypes from "../fixtureTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import { MetricCard } from "./MetricCard";
import visual from "./PromptAB.module.css";

/** Reference: screens/Prompts.jsx; EXAMPLE ONLY. */
export const PromptAB = ({ prompt }: { prompt: E.Prompt }) => {
  const { t } = useI18n();
  const ab = FIX_PROMPT_AB;
  return <PromptABAbAccuracy {...{ t, prompt, ab }} />;
};

interface PromptABAbAccuracyProps {
  t: (key: string, fallback?: string) => string;
  prompt: FixtureTypes.Prompt;
  ab: {
    prompt_id: string;
    a: {
      version: string;
      accuracy: number;
      latency_ms: number;
      cost_per_1k: number;
      sample_output: string;
    };
    b: {
      version: string;
      accuracy: number;
      latency_ms: number;
      cost_per_1k: number;
      sample_output: string;
    };
    n_samples: number;
    winner: string;
    significant: boolean;
    p_value: number;
  };
}

function PromptABAbAccuracy({ t, prompt, ab }: PromptABAbAccuracyProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="fork" size={12} className={visual.surface} />
        <span className={visual.label}>
          {t("pr.abTitle")} · {prompt.name}
        </span>
        <span className="chip">n={ab.n_samples}</span>
        {ab.significant && (
          <span className={`chip ${visual.surface2 ?? ""}`}>
            {t("pr.abSig")}
            {ab.p_value}
          </span>
        )}
        <span className={visual.caption}>
          {t("pr.abWinner")} <span className={visual.surface3}>{ab.winner.toUpperCase()}</span>
        </span>
      </div>
      <PromptABAbAccuracy2 {...{ ab, t }} />
    </div>
  );
}

interface PromptABAbAccuracy2Props {
  ab: {
    prompt_id: string;
    a: {
      version: string;
      accuracy: number;
      latency_ms: number;
      cost_per_1k: number;
      sample_output: string;
    };
    b: {
      version: string;
      accuracy: number;
      latency_ms: number;
      cost_per_1k: number;
      sample_output: string;
    };
    n_samples: number;
    winner: string;
    significant: boolean;
    p_value: number;
  };
  t: (key: string, fallback?: string) => string;
}

function PromptABAbAccuracy2({ ab, t }: PromptABAbAccuracy2Props) {
  return (
    <div className={visual.grid}>
      {(
        [
          ["a", ab.a],
          ["b", ab.b],
        ] as const
      ).map(([k, v]) => (
        <div
          key={k}
          className={visual.column}
          style={{ borderRight: k === "a" ? "1px solid var(--border)" : "none" }}
        >
          <div className={visual.row2}>
            <span
              className={visual.row3}
              style={{
                background: k === ab.winner ? "var(--accent)" : "var(--bg-raised)",
                color: k === ab.winner ? "#fff" : "var(--fg-muted)",
              }}
            >
              {k.toUpperCase()}
            </span>
            <span className={`mono ${visual.label2 ?? ""}`}>{v.version}</span>
            {k === ab.winner && (
              <span className={`chip ${visual.surface4 ?? ""}`}>
                <Icon name="check" size={9} /> {t("pr.abWinnerLabel")}
              </span>
            )}
          </div>
          <PromptABAbAccuracy3 {...{ t, v }} />
          <div>
            <div className={visual.caption2}>{t("pr.abSample")}</div>
            <pre className={visual.label3}>{v.sample_output}</pre>
          </div>
        </div>
      ))}
    </div>
  );
}

interface PromptABAbAccuracy3Props {
  t: (key: string, fallback?: string) => string;
  v: {
    version: string;
    accuracy: number;
    latency_ms: number;
    cost_per_1k: number;
    sample_output: string;
  };
}

function PromptABAbAccuracy3({ t, v }: PromptABAbAccuracy3Props) {
  return (
    <div className={visual.grid2}>
      <MetricCard
        label={t("pr.abAccuracy")}
        value={`${(v.accuracy * 100).toFixed(1)}%`}
        bar={v.accuracy}
        barColor={v.accuracy > 0.87 ? "var(--success)" : "var(--warn)"}
      />
      <MetricCard
        label={t("pr.abLatency")}
        value={`${String(v.latency_ms)}ms`}
        bar={v.latency_ms / 2000}
        barColor="var(--warn)"
      />
      <MetricCard
        label={t("pr.abCost")}
        value={`$${v.cost_per_1k.toFixed(2)}`}
        bar={v.cost_per_1k / 1}
        barColor="var(--accent)"
      />
    </div>
  );
}
