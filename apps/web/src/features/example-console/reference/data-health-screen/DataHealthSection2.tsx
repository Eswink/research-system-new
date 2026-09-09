import { type Dispatch, type SetStateAction } from "react";
import visual from "../DataHealthScreen.module.css";
import { DH_METRICS } from "../dhMetrics";
import { DataHealthSection4 } from "./DataHealthSection4";

interface DataHealthSection2Props {
  t: (key: string, fallback?: string) => string;
  health: (m: (typeof DH_METRICS)[number]) => { tone: string; label: string; icon: string };
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
}

export function DataHealthSection2({
  t,
  health,
  selectedId,
  setSelectedId,
}: DataHealthSection2Props) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.label}>{t("dh.overview")}</div>
      <DataHealthSection4 {...{ t, health, selectedId, setSelectedId }} />
    </div>
  );
}
