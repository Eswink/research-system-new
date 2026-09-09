import type * as E from "../../exampleTypes";
import visual from "../EvaluationSection.module.css";
import { Icon } from "../Icon";
import { INPUT_ERR } from "../inputErr";
import { INPUT } from "../protocolInput";

interface EvaluationSectionSection2Props {
  setP: E.UpdateProtocol;
  ev: { benchmarks: string[]; languages: string[]; n_per_lang: number; temperature_grid: number[] };
  eN: E.ProtocolIssue | undefined;
  wN: E.ProtocolIssue | undefined;
}

export function EvaluationSectionSection2({ setP, ev, eN, wN }: EvaluationSectionSection2Props) {
  return (
    <div className={visual.row6}>
      <button
        className="btn sm"
        onClick={() => {
          setP((p) => {
            p.evaluation.n_per_lang = Math.max(0, p.evaluation.n_per_lang - 50);
          });
        }}
      >
        <Icon name="dot" size={9} /> −50
      </button>
      <input
        type="number"
        value={ev.n_per_lang}
        onChange={(e) => {
          setP((p) => {
            p.evaluation.n_per_lang = Number(e.target.value);
          });
        }}
        style={{
          ...(eN ? INPUT_ERR : wN ? { ...INPUT, borderColor: "var(--warn-line)" } : INPUT),
          fontFamily: "var(--font-mono)",
          width: 96,
          textAlign: "center",
        }}
      />
      <button
        className="btn sm"
        onClick={() => {
          setP((p) => {
            p.evaluation.n_per_lang += 50;
          });
        }}
      >
        <Icon name="plus" size={9} /> +50
      </button>
      <span className={visual.caption3}>
        × {ev.languages.length} = {(ev.n_per_lang * ev.languages.length).toLocaleString()} samples
      </span>
    </div>
  );
}
