import type { PreflightReportDto } from "../../api/types";

export function ReportView({ report }: { report: PreflightReportDto }) {
  const costText =
    report.estimated_cost === null
      ? "not estimated"
      : `${String(report.estimated_cost)} USD`;
  return (
    <div data-testid="dry-run-report">
      <p>
        Preflight status: <strong data-testid="preflight-status">{report.status}</strong> ·
        estimated cost: {costText}
      </p>
      {report.findings.length > 0 && (
        <ul>
          {report.findings.map((finding, index) => (
            <li key={`${finding.code}-${String(index)}`}>
              [{finding.severity}] {finding.message}
            </li>
          ))}
        </ul>
      )}
      {report.unresolved_risks.length > 0 && (
        <p data-testid="dry-run-risks">Risks: {report.unresolved_risks.join("; ")}</p>
      )}
    </div>
  );
}