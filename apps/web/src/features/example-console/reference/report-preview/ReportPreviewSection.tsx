import type * as FixtureTypes from "../../fixtureTypes";
import { DigestText } from "../DigestText";
import { Icon } from "../Icon";
import visual from "../ReportPreview.module.css";
import { ReportStatusBadge } from "../ReportStatusBadge";
import { ReportPreviewSection2 } from "./ReportPreviewSection2";

interface ReportPreviewSectionProps {
  report: FixtureTypes.Report;
  t: (key: string, fallback?: string) => string;
  onEdit: () => void;
  showDraft: boolean;
  draft: {
    id: string;
    sections: { id: string; title: string; status: string; claims: string[] }[];
  };
}

export function ReportPreviewSection({
  report,
  t,
  onEdit,
  showDraft,
  draft,
}: ReportPreviewSectionProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <div className={visual.surface}>
          <div className={visual.caption}>
            {report.format} · {report.pdf_pages}
            {t("rp.pages")} · {report.word_count.toLocaleString()} {t("rp.words")}
          </div>
          <div className={visual.label}>{report.title}</div>
          <div className={visual.row2}>
            <ReportStatusBadge status={report.status} />
            <DigestText value={report.digest} label="digest:" length={10} />
            {report.doi && <span className="mono">DOI: {report.doi}</span>}
            {report.venue && <span className="chip">{report.venue}</span>}
          </div>
        </div>
        <div className={visual.row3}>
          <button className="btn sm" onClick={onEdit}>
            <Icon name="copy" size={10} /> {t("act.edit")}
          </button>
          <button className="btn sm">
            <Icon name="external" size={10} /> {t("act.preview")}
          </button>
          <button className="btn primary sm">
            <Icon name="external" size={10} /> {t("act.export")}
          </button>
        </div>
      </div>

      <ReportPreviewSection2 {...{ report, t, showDraft, draft }} />
    </div>
  );
}
