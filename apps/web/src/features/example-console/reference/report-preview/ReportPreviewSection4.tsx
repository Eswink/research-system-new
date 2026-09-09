import FIX_CLAIMS from "../../data/claims.json";
import { ClaimStatusBadge } from "../ClaimStatusBadge";
import visual from "../ReportPreview.module.css";

interface ReportPreviewSection4Props {
  t: (key: string, fallback?: string) => string;
  s: { id: string; title: string; status: string; claims: string[] };
}

export function ReportPreviewSection4({ t, s }: ReportPreviewSection4Props) {
  return (
    <div className={visual.surface5}>
      <div className={visual.caption4}>{t("rp.cited")}</div>
      <div className={visual.column2}>
        {s.claims.map((cid) => {
          const c = FIX_CLAIMS.find((x) => x.id === cid);
          if (!c) return null;
          return (
            <div key={cid} className={visual.row5}>
              <ClaimStatusBadge status={c.status} />
              <div className={visual.label7}>
                <span className={visual.caption5}>[{cid.slice(4, 14)}]</span> {c.statement}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
