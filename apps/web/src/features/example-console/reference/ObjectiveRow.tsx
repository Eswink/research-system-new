import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import visual from "./ObjectiveRow.module.css";

/** Reference: components/AppShell.jsx; EXAMPLE ONLY. */
export const ObjectiveRow = ({
  id,
  statement,
  status,
}: {
  id: string;
  statement: string;
  status: string;
}) => {
  const { t } = useI18n();
  const label = status === "ongoing" ? t("ov.status.ongoing") : t("ov.status.pending");
  return (
    <div className={visual.grid}>
      <Icon
        name={status === "ongoing" ? "spin" : "circle-o"}
        size={12}
        className={visual.surface}
        style={{ color: status === "ongoing" ? "var(--accent)" : "var(--fg-faint)" }}
      />
      <div>
        <div className={visual.label}>{statement}</div>
        <span className={`mono ${visual.caption ?? ""}`}>{id}</span>
      </div>
      <span
        className="chip"
        style={{
          color: status === "ongoing" ? "var(--accent)" : "var(--fg-muted)",
          borderColor: status === "ongoing" ? "var(--accent-line)" : "var(--border)",
        }}
      >
        {label}
      </span>
    </div>
  );
};
