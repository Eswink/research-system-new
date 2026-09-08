import { useI18n } from "../i18n/useI18n";

/** 未知地址的明确未找到页（T06：每条规范路由有独立身份，未知不静默回退）。 */
export function NotFoundPage({ onHome }: { onHome: () => void }) {
  const { t } = useI18n();
  return (
    <div style={{ padding: 48, textAlign: "center" }} data-testid="not-found">
      <div
        className="mono"
        style={{ fontSize: 11, color: "var(--fg-faint)", letterSpacing: "0.08em" }}
      >
        404
      </div>
      <h2 style={{ fontSize: "var(--fs-title)", fontWeight: 500, margin: "8px 0" }}>
        {t("notfound.title")}
      </h2>
      <p style={{ color: "var(--fg-muted)", fontSize: "var(--fs-meta)" }}>
        {t("notfound.hint")}
      </p>
      <button type="button" className="btn primary" onClick={onHome} style={{ marginTop: 16 }}>
        {t("notfound.home")}
      </button>
    </div>
  );
}
