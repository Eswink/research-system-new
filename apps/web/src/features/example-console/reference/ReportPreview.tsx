import FIX_REPORT_DRAFT from "../data/report-draft.json";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { ReportPreviewSection } from "./report-preview/ReportPreviewSection";

export const ReportPreview = ({ report, onEdit }: { report: E.Report; onEdit: () => void }) => {
  const { t } = useI18n();
  const draft = FIX_REPORT_DRAFT;
  const showDraft = report.id === draft.id;

  return <ReportPreviewSection {...{ report, t, onEdit, showDraft, draft }} />;
};
