import FIX_CLAIMS from "../../data/claims.json";
import { ClaimStatusBadge } from "../ClaimStatusBadge";
import visual from "../NotebooksScreen.module.css";
import { Notebooksul } from "./Notebooksul";

interface NotebooksSection2Props {
  selected: {
    id: string;
    title: string;
    author: string;
    updated_at: string;
    word_count: number;
    linked_claims: string[];
    linked_runs: string[];
    excerpt: string;
  };
  t: (key: string, fallback?: string) => string;
}

export function NotebooksSection2({ selected, t }: NotebooksSection2Props) {
  return (
    <div className={visual.column2}>
      <p className={visual.label4}>{selected.excerpt}</p>
      <p className={visual.label5}>
        The dataset in question is{" "}
        <span className={`mono ${visual.surface6 ?? ""}`}>ds_medqa_multi_v3</span>, which we sampled
        at n=1200 per language. Below is a summary of the pattern I observed while browsing the
        failure cases:
      </p>
      <Notebooksul {...{}} />
      <p className={visual.label7}>
        Next step: instrument the eval harness to bucket errors by category and re-run the Spanish
        subset with a stricter normalization step. Filed as{" "}
        <span className={`mono ${visual.surface7 ?? ""}`}>exp_q_01K5FZ8P2M3N</span>.
      </p>

      {selected.linked_claims.length > 0 && (
        <div className={visual.surface8}>
          <div className={visual.caption3}>
            {t("nb.linkedClaims")} {selected.linked_claims.length}
          </div>
          {selected.linked_claims.map((cid) => {
            const c = FIX_CLAIMS.find((x) => x.id === cid);
            if (!c) return null;
            return (
              <div key={cid} className={visual.row4}>
                <ClaimStatusBadge status={c.status} />
                <div className={visual.label8}>{c.statement}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
