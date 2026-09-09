import { type Dispatch, type SetStateAction } from "react";
import visual from "../DataHealthScreen.module.css";
import { DH_METRICS } from "../dhMetrics";
import { Icon } from "../Icon";
import { DataHealthSchemaOk } from "./DataHealthSchemaOk";
import { DataHealthSection2 } from "./DataHealthSection2";

interface DataHealthSectionProps {
  t: (key: string, fallback?: string) => string;
  health: (m: (typeof DH_METRICS)[number]) => { tone: string; label: string; icon: string };
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
  selected:
    | {
        id: string;
        dataset: string;
        rows: number;
        drift: number;
        freshness_d: number;
        pii_hits: number;
        label_skew: number;
        schema_ok: boolean;
      }
    | undefined;
}

export function DataHealthSection({
  t,
  health,
  selectedId,
  setSelectedId,
  selected,
}: DataHealthSectionProps) {
  return (
    <div className={visual.grid2}>
      <DataHealthSection2 {...{ t, health, selectedId, setSelectedId }} />

      {selected && (
        <div className={`panel ${visual.panel2 ?? ""}`}>
          <div className={visual.surface5}>
            <div className={visual.caption}>{t("dh.detail")}</div>
            <div className={visual.label8}>{selected.dataset}</div>
          </div>
          <DataHealthSchemaOk {...{ t, selected }} />

          <div className={visual.row4}>
            <button className="btn sm">
              <Icon name="spin" size={11} /> {t("dh.rescan")}
            </button>
            <button className={`btn sm ghost ${visual.action ?? ""}`}>
              <Icon name="external" size={11} /> {t("dh.openDataset")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
