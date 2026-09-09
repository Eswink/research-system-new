import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ReportPreview.module.css";
import { ReportPreviewSection3 } from "./ReportPreviewSection3";

interface ReportPreviewSection2Props {
  report: FixtureTypes.Report;
  t: (key: string, fallback?: string) => string;
  showDraft: boolean;
  draft: {
    id: string;
    sections: { id: string; title: string; status: string; claims: string[] }[];
  };
}

export function ReportPreviewSection2({ report, t, showDraft, draft }: ReportPreviewSection2Props) {
  return (
    <div className={visual.surface2}>
      {/* Paper-styled document */}
      <ReportPreviewSection3 {...{ report, t, showDraft, draft }} />
    </div>
  );
}
