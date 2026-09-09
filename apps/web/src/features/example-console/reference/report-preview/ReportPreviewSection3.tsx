import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ReportPreview.module.css";
import { SectionStatusChip } from "../SectionStatusChip";
import { sectionText } from "../sectionText";
import { ReportPreviewSection4 } from "./ReportPreviewSection4";

interface ReportPreviewSection3Props {
  report: FixtureTypes.Report;
  t: (key: string, fallback?: string) => string;
  showDraft: boolean;
  draft: {
    id: string;
    sections: { id: string; title: string; status: string; claims: string[] }[];
  };
}

export function ReportPreviewSection3({ report, t, showDraft, draft }: ReportPreviewSection3Props) {
  return (
    <div className={visual.surface3}>
      <div className={visual.surface4}>
        <div className={visual.label2}>{report.title}</div>
        <div className={visual.label3}>{report.authors.join(" · ")}</div>
        <div className={visual.caption2}>
          {report.published_at
            ? `${t("rp.published")} ${new Date(report.published_at).toISOString().slice(0, 10)}`
            : `${t("rp.draft")} ${new Date(report.updated_at).toISOString().slice(0, 10)}`}
        </div>
      </div>

      {showDraft ? <DraftReportSections draft={draft} t={t} /> : <PublishedReportPreview t={t} />}
    </div>
  );
}

function DraftReportSections({ draft, t }: Pick<ReportPreviewSection3Props, "draft" | "t">) {
  return (
    <div className={visual.column}>
      {draft.sections.map((section) => (
        <div key={section.id}>
          <div className={visual.row4}>
            <span className={visual.label4}>{section.title}</span>
            <SectionStatusChip status={section.status} />
            {section.claims.length > 0 && (
              <span className={`chip ${visual.caption3 ?? ""}`}>
                {t("rp.cites")} {section.claims.length}
              </span>
            )}
          </div>
          {section.status === "todo" ? (
            <div className={visual.label5}>{t("rp.sectTodo")}</div>
          ) : (
            <>
              <p className={visual.label6}>{sectionText(section.id)}</p>
              {section.claims.length > 0 && <ReportPreviewSection4 t={t} s={section} />}
            </>
          )}
        </div>
      ))}
    </div>
  );
}

function PublishedReportPreview({ t }: Pick<ReportPreviewSection3Props, "t">) {
  return (
    <div className={visual.column3}>
      <p className={visual.label8}>
        <strong className={visual.surface6}>{t("rp.abstract")}</strong> {sectionText("abstract")}
      </p>
      <p className={visual.label9}>{sectionText("intro")}</p>
      <p className={visual.label10}>{sectionText("methods")}</p>
      <p className={visual.label11}>{sectionText("results")}</p>
    </div>
  );
}
