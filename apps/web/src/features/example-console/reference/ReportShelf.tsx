import FIX_REPORTS from "../data/reports.json";
import { Icon } from "./Icon";
import styles from "./ReportShelf.module.css";
import { ReportStatusBadge } from "./ReportStatusBadge";

export function ReportShelf({ onOpen }: { onOpen: (id: string) => void }) {
  return (
    <div className={styles.shelf} data-testid="report-shelf">
      {FIX_REPORTS.map((report) => (
        <button
          key={report.id}
          type="button"
          className={styles.book}
          onClick={() => {
            onOpen(report.id);
          }}
        >
          <Icon name="book" size={24} />
          <strong>{report.title}</strong>
          <ReportStatusBadge status={report.status} />
          <span className="mono">
            {report.format} · {report.pdf_pages} pp
          </span>
        </button>
      ))}
    </div>
  );
}
