import { type Dispatch, type SetStateAction } from "react";
import { DigestText } from "../DigestText";
import { UnknownValue } from "../UnknownValue";
import visual from "../WorkspaceScreen.module.css";
import { WorkspaceStateReprod } from "./WorkspaceStateReprod";
import { WorkspaceStateReprod6 } from "./WorkspaceStateReprod6";

interface WorkspaceStateReprod3Props {
  t: (key: string, fallback?: string) => string;
  setSelectedExp: Dispatch<SetStateAction<string>>;
  selectedExp: string;
  exp:
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
      }
    | undefined;
}

export function WorkspaceStateReprod3({
  t,
  setSelectedExp,
  selectedExp,
  exp,
}: WorkspaceStateReprod3Props) {
  return (
    <div className={visual.column}>
      {/* Experiment table */}
      <WorkspaceStateReprod {...{ t, setSelectedExp, selectedExp }} />

      {/* Selected experiment digests */}
      {exp && (
        <div className={`panel ${visual.panel3 ?? ""}`}>
          <WorkspaceStateReprod6 {...{ exp, t }} />
          <div className={visual.grid2}>
            <div>
              <div className={visual.caption4}>{t("ws.imageDigest")}</div>
              {exp.image_digest ? (
                <DigestText value={exp.image_digest} length={16} />
              ) : (
                <UnknownValue hint={t("ws.imageMissing")} />
              )}
            </div>
            <div>
              <div className={visual.caption5}>{t("ws.envDigest")}</div>
              <DigestText value={exp.environment_digest} length={16} />
            </div>
          </div>
          {exp.reproduction_note && (
            <div className={visual.label8}>
              <div className={visual.caption6}>{t("ws.repNote")}</div>
              {exp.reproduction_note}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
