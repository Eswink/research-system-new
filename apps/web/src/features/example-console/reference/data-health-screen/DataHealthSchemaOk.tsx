import visual from "../DataHealthScreen.module.css";
import { Icon } from "../Icon";
import { StatusBadge } from "../StatusBadge";
import { DataHealthSection3 } from "./DataHealthSection3";
import { DataHealthSection5 } from "./DataHealthSection5";

interface DataHealthSchemaOkProps {
  t: (key: string, fallback?: string) => string;
  selected: {
    id: string;
    dataset: string;
    rows: number;
    drift: number;
    freshness_d: number;
    pii_hits: number;
    label_skew: number;
    schema_ok: boolean;
  };
}

export function DataHealthSchemaOk({ t, selected }: DataHealthSchemaOkProps) {
  return (
    <div className={visual.column2}>
      {/* Drift chart */}
      <DataHealthSection3 {...{ t, selected }} />

      {/* Label distribution */}
      <DataHealthSection5 {...{ t }} />

      {/* PII scan */}
      {selected.pii_hits > 0 && (
        <div>
          <div className={visual.caption7}>{t("dh.piiScan")}</div>
          <div className={visual.row3}>
            <Icon name="warn-tri" size={13} />
            <div>
              <div className={visual.surface7}>
                {selected.pii_hits} {t("dh.piiFound")}
              </div>
              <div className={visual.caption8}>{t("dh.piiHint")}</div>
            </div>
          </div>
        </div>
      )}

      {/* Schema */}
      <div>
        <div className={visual.caption9}>{t("dh.schema")}</div>
        {selected.schema_ok ? (
          <StatusBadge tone="success" icon="check" label={t("dh.schemaOk")} filled />
        ) : (
          <div className={visual.label11}>
            <div className={visual.surface8}>{t("dh.schemaMissing")}</div>
            <div className={`mono ${visual.caption10 ?? ""}`}>+ column "context_length" (int)</div>
            <div className={`mono ${visual.caption11 ?? ""}`}>- column "region" (str)</div>
          </div>
        )}
      </div>
    </div>
  );
}
