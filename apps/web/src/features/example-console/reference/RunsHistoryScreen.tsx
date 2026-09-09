import { useState } from "react";
import FIX_RUNS_HISTORY from "../data/runs-history.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { RunDiffView } from "./RunDiffView";
import visual from "./RunsHistoryScreen.module.css";
import { RunsHistorySection } from "./runs-history-screen/RunsHistorySection";
import { RunsHistoryTitle } from "./runs-history-screen/RunsHistoryTitle";

export const RunsHistoryScreen = () => {
  const { t } = useI18n();
  const [view, setView] = useState("list"); // list | diff
  const [selectedIds, setSelectedIds] = useState(["run_01K5FZ8G3X2QN4M", "run_01K5FZ8G2X1QN3L"]);
  const [q, setQ] = useState("");
  const filtered = q
    ? FIX_RUNS_HISTORY.filter((r) => r.label.toLowerCase().includes(q.toLowerCase()))
    : FIX_RUNS_HISTORY;

  return (
    <div className={visual.column}>
      <RunsHistoryTitle {...{ t, q, setQ, view, setView, selectedIds }} />

      {view === "list" && (
        <div className={`panel ${visual.panel ?? ""}`}>
          <div className={`row head ${visual.surface ?? ""}`}>
            <span></span>
            <span>{t("rh.colRun")}</span>
            <span>{t("lbl.state")}</span>
            <span>{t("lbl.duration")}</span>
            <span>{t("lbl.tasks")}</span>
            <span>{t("lbl.spent")}</span>
            <span>{t("lbl.autonomy")}</span>
            <span>{t("lbl.started")}</span>
          </div>
          <RunsHistorySection {...{ filtered, selectedIds, setSelectedIds, t }} />
          <div className={visual.row2}>
            <span>
              {selectedIds.length}/2 {t("rh.selected")}
            </span>
            <span>
              {filtered.length} {t("rh.runsN")} ·{" "}
              {filtered.filter((r) => r.state === "SUCCEEDED").length} {t("rh.succeeded")} ·{" "}
              {filtered.filter((r) => r.state === "FAILED").length} {t("rh.failed")}
            </span>
          </div>
        </div>
      )}

      {view === "diff" && <RunDiffView aId={selectedIds[0]} bId={selectedIds[1]} />}
    </div>
  );
};
