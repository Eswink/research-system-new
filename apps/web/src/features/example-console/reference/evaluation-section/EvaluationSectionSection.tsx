import type * as E from "../../exampleTypes";
import { AVAILABLE_LANGUAGES } from "../availableLanguages";
import visual from "../EvaluationSection.module.css";
import { Icon } from "../Icon";

interface EvaluationSectionSectionProps {
  ev: { benchmarks: string[]; languages: string[]; n_per_lang: number; temperature_grid: number[] };
  setP: E.UpdateProtocol;
}

export function EvaluationSectionSection({ ev, setP }: EvaluationSectionSectionProps) {
  return (
    <div>
      <div className={visual.row}>
        {ev.languages.map((code) => {
          const meta = AVAILABLE_LANGUAGES.find((l) => l.code === code);
          return (
            <span key={code} className={visual.row2}>
              <span className={`mono ${visual.surface ?? ""}`}>{code}</span>
              {meta && <span className={visual.caption}>{meta.label}</span>}
              <button
                onClick={() => {
                  setP((p) => {
                    p.evaluation.languages = p.evaluation.languages.filter((x) => x !== code);
                  });
                }}
                className={visual.row3}
              >
                <Icon name="x" size={9} />
              </button>
            </span>
          );
        })}
      </div>
      <div className={visual.row4}>
        {AVAILABLE_LANGUAGES.filter((l) => !ev.languages.includes(l.code)).map((l) => (
          <button
            key={l.code}
            onClick={() => {
              setP((p) => {
                p.evaluation.languages.push(l.code);
              });
            }}
            className={visual.row5}
          >
            <Icon name="plus" size={9} />
            <span className="mono">{l.code}</span>
            <span className={visual.caption2}>{l.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
