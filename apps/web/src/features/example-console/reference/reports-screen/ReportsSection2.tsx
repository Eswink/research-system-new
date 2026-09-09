import { type Dispatch, type SetStateAction } from "react";
import FIX_REPORTS from "../../data/reports.json";
import { Icon } from "../Icon";
import visual from "../ReportsScreen.module.css";
import { ReportStatusBadge } from "../ReportStatusBadge";

interface ReportsSection2Props {
  t: (key: string, fallback?: string) => string;
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
}

export function ReportsSection2({ t, selectedId, setSelectedId }: ReportsSection2Props) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="book" size={12} className={visual.surface} />
        <span className={visual.label}>{t("rp.title")}</span>
        <span className="chip">{FIX_REPORTS.length}</span>
      </div>
      <div className={visual.surface2}>
        {FIX_REPORTS.map((r) => {
          const active = r.id === selectedId;
          return (
            <div
              key={r.id}
              onClick={() => {
                setSelectedId(r.id);
              }}
              className={visual.surface3}
              style={{
                background: active ? "var(--bg-hover)" : "transparent",
                borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
              }}
            >
              <div className={visual.row2}>
                <ReportStatusBadge status={r.status} />
                <span className={`chip ${visual.caption ?? ""}`}>{r.format}</span>
              </div>
              <div className={visual.label2}>{r.title}</div>
              <div className={visual.row3}>
                <span>{r.sections} sect</span>
                <span>{r.cited_claims} claims</span>
                <span>{r.figures} figs</span>
                <span>{r.pdf_pages}pp</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
