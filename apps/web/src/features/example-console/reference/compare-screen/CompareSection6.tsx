import visual from "../CompareScreen.module.css";
import { Icon } from "../Icon";

interface CompareSection6Props {
  t: (key: string, fallback?: string) => string;
  manifestFields: (
    | { field: string; a: string; b: string; note: string }
    | { field: string; a: number; b: number; note: string }
  )[];
  visibleManifest: (
    | { field: string; a: string; b: string; note: string }
    | { field: string; a: number; b: number; note: string }
  )[];
}

export function CompareSection6({ t, manifestFields, visibleManifest }: CompareSection6Props) {
  return (
    <div className={`panel ${visual.panel2 ?? ""}`}>
      <div className={visual.row6}>
        <Icon name="book" size={12} />
        <span className={visual.label3}>{t("cmp.manifest")}</span>
        <span className={`chip ${visual.surface5 ?? ""}`}>
          {manifestFields.filter((f) => f.note !== "unchanged").length} {t("cmp.changed")} /{" "}
          {manifestFields.length} {t("cmp.total")}
        </span>
      </div>
      <div className={visual.surface6}>
        <div className={`row head ${visual.surface7 ?? ""}`}>
          <span>{t("cmp.field")}</span>
          <span>A</span>
          <span>B</span>
          <span>{t("cmp.note")}</span>
        </div>
        {visibleManifest.map((f) => (
          <div key={f.field} className={`row ${visual.surface8 ?? ""}`}>
            <div className={`mono ${visual.label4 ?? ""}`}>{f.field}</div>
            <div
              className={`mono ${visual.label5 ?? ""}`}
              style={{ color: f.a !== f.b ? "var(--fg)" : "var(--fg-faint)" }}
            >
              {String(f.a).slice(0, 30)}
            </div>
            <div
              className={`mono ${visual.label6 ?? ""}`}
              style={{ color: f.a !== f.b ? "var(--accent)" : "var(--fg-faint)" }}
            >
              {String(f.b).slice(0, 30)}
            </div>
            <div
              className={visual.caption2}
              style={{ color: f.note === "unchanged" ? "var(--fg-faint)" : "var(--warn)" }}
            >
              {f.note}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
