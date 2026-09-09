import visual from "../WorkspaceScreen.module.css";

interface WorkspaceSectionProps {
  e:
    | {
        experiment_run_id: string;
        label: string;
        metrics: {
          hallucination_rate_en: number;
          hallucination_rate_es: number;
          hallucination_rate_zh: number;
          chi2: number;
          p_value: number;
          n: number;
          variance_opus?: never;
          variance_sonnet?: never;
          variance_gpt4o?: never;
          n_per_lang?: never;
          cot_hall_rate?: never;
          baseline_hall_rate?: never;
          overconfidence_delta?: never;
          note?: never;
        };
        image_digest: string;
        environment_digest: string;
        reproduction_available: boolean;
        started_at: string;
        duration_s: number;
        reproduction_note?: never;
      }
    | {
        experiment_run_id: string;
        label: string;
        metrics: {
          variance_opus: number;
          variance_sonnet: number;
          variance_gpt4o: number;
          n_per_lang: number;
          hallucination_rate_en?: never;
          hallucination_rate_es?: never;
          hallucination_rate_zh?: never;
          chi2?: never;
          p_value?: never;
          n?: never;
          cot_hall_rate?: never;
          baseline_hall_rate?: never;
          overconfidence_delta?: never;
          note?: never;
        };
        image_digest: string;
        environment_digest: string;
        reproduction_available: boolean;
        started_at: string;
        duration_s: number;
        reproduction_note?: never;
      }
    | {
        experiment_run_id: string;
        label: string;
        metrics: {
          cot_hall_rate: number;
          baseline_hall_rate: number;
          overconfidence_delta: number;
          n: number;
          hallucination_rate_en?: never;
          hallucination_rate_es?: never;
          hallucination_rate_zh?: never;
          chi2?: never;
          p_value?: never;
          variance_opus?: never;
          variance_sonnet?: never;
          variance_gpt4o?: never;
          n_per_lang?: never;
          note?: never;
        };
        image_digest: string;
        environment_digest: string;
        reproduction_available: boolean;
        started_at: string;
        duration_s: number;
        reproduction_note?: never;
      }
    | {
        experiment_run_id: string;
        label: string;
        metrics: {
          note: string;
          hallucination_rate_en?: never;
          hallucination_rate_es?: never;
          hallucination_rate_zh?: never;
          chi2?: never;
          p_value?: never;
          n?: never;
          variance_opus?: never;
          variance_sonnet?: never;
          variance_gpt4o?: never;
          n_per_lang?: never;
          cot_hall_rate?: never;
          baseline_hall_rate?: never;
          overconfidence_delta?: never;
        };
        image_digest: null;
        environment_digest: string;
        reproduction_available: boolean;
        reproduction_note: string;
        started_at: string;
        duration_s: number;
      };
}

export function WorkspaceSection({ e }: WorkspaceSectionProps) {
  return (
    <div className={visual.row3}>
      {Object.entries(e.metrics)
        .slice(0, 3)
        .map(([k, v]) => (
          <span key={k} className={visual.caption2}>
            <span className={visual.surface10}>{k}</span>=
            {typeof v === "number" ? (v < 1 ? v.toFixed(3) : v.toString()) : String(v).slice(0, 20)}
          </span>
        ))}
    </div>
  );
}
