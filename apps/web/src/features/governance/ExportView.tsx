import type { ExportBundleDto } from "../../api/types";
import { PanelSection } from "../../components/PanelSection";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

/** This is the API's JSON bundle, not a signed report, PDF, publication or evidence generation. */
export function ExportView({ bundle, runId }: { bundle: ExportBundleDto; runId: string }) {
  const { language, t } = useI18n();
  const matches = bundle.run_id === runId;
  return (
    <PanelSection title={t("audit.export")}>
      <div className={styles.page}>
        <KeyValueList
          fields={[
            { label: "Run", value: bundle.run_id },
            { label: "State", value: bundle.run_state },
            { label: "Manifest", value: bundle.manifest_digest ?? "NOT FROZEN" },
            { label: "Export source", value: bundle.exported_from },
            { label: "Claims", value: bundle.claims.length },
            { label: "Evidence", value: bundle.evidence.length },
            { label: "Usage entries", value: bundle.usage.entries.length },
          ]}
        />
        <p className={styles.notice}>{t("audit.exportNote")}</p>
        {!matches && (
          <p role="alert" className={styles.notice}>
            {language === "zh"
              ? "返回的导出包与当前 Run 不匹配，已阻止下载。"
              : "Exported run does not match the selection; download blocked."}
          </p>
        )}
        <button
          type="button"
          className="btn primary"
          disabled={!matches}
          onClick={() => {
            if (matches) downloadBundle(bundle);
          }}
        >
          {t("audit.download")}
        </button>
      </div>
    </PanelSection>
  );
}

function downloadBundle(bundle: ExportBundleDto): void {
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${bundle.run_id.replaceAll(/[^A-Za-z0-9_-]/g, "_")}-export.json`;
  anchor.click();
  window.setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 1000);
}
