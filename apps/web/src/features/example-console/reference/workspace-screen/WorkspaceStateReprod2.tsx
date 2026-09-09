import { type Dispatch, type SetStateAction } from "react";
import { FileNode } from "../FileNode";
import { Icon } from "../Icon";
import visual from "../WorkspaceScreen.module.css";
import { WorkspaceStateReprod3 } from "./WorkspaceStateReprod3";

interface WorkspaceStateReprod2Props {
  t: (key: string, fallback?: string) => string;
  workspace: (
    | {
        path: string;
        type: string;
        children: (
          | {
              path: string;
              type: string;
              children: { path: string; type: string; size: string; modified: string }[];
              size?: never;
              modified?: never;
            }
          | { path: string; type: string; size: string; modified: string; children?: never }
        )[];
      }
    | {
        path: string;
        type: string;
        children: (
          | { path: string; type: string; size: string; modified: string; highlight: boolean }
          | { path: string; type: string; size: string; modified: string; highlight?: never }
        )[];
      }
  )[];
  selectedFile: string;
  setSelectedFile: Dispatch<SetStateAction<string>>;
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

export function WorkspaceStateReprod2({
  t,
  workspace,
  selectedFile,
  setSelectedFile,
  setSelectedExp,
  selectedExp,
  exp,
}: WorkspaceStateReprod2Props) {
  return (
    <div className={visual.grid}>
      {/* Left: workspace tree */}
      <div className={`panel ${visual.panel ?? ""}`}>
        <div className={visual.row}>
          <Icon name="hex" size={12} className={visual.surface} />
          <span className={visual.label}>{t("ws.snapshot")}</span>
          <span className={`chip ${visual.surface2 ?? ""}`}>
            <Icon name="lock" size={9} /> {t("ws.readOnly")}
          </span>
        </div>
        <div className={visual.caption}>
          {t("ws.snapshotId")} ws_snap_01K5FZ8H_r24 · {t("ws.at")} 14:36:12Z
        </div>
        <div className={visual.label2}>
          {workspace.map((node) => (
            <FileNode
              key={node.path}
              node={node}
              depth={0}
              selected={selectedFile}
              onSelect={setSelectedFile}
            />
          ))}
        </div>
      </div>

      {/* Right: experiments + selected file preview */}
      <WorkspaceStateReprod3 {...{ t, setSelectedExp, selectedExp, exp }} />
    </div>
  );
}
