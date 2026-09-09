import { useState } from "react";
import FIX_REPORTS from "../data/reports.json";
import type * as E from "../exampleTypes";
import { requiredExample } from "../requiredExample";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import { PageToolbar } from "./PageToolbar";
import { ReportShelf } from "./ReportShelf";
import visual from "./ReportsScreen.module.css";
import { ViewSwitcher } from "./ViewSwitcher";
import { ReportsDetailsDrawer } from "./reports-screen/ReportsDetailsDrawer";
import { ReportsSection } from "./reports-screen/ReportsSection";

export const ReportsScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState(requiredExample(FIX_REPORTS[0]).id);
  const [drawer, setDrawer] = useState<E.ReportDrawer | null>(null);
  const [view, setView] = useState("list");
  const selected = FIX_REPORTS.find((r) => r.id === selectedId);

  return (
    <div className={visual.column}>
      <PageToolbar title={t("rp.title")} subtitle={t("rp.subtitle")}>
        <ViewSwitcher
          value={view}
          onChange={setView}
          views={[
            { value: "list", label: t("rp.viewList"), icon: "menu" },
            { value: "shelf", label: t("rp.viewShelf"), icon: "book" },
          ]}
        />
        <button
          className="btn primary sm"
          onClick={() => {
            setDrawer({ mode: "create" });
          }}
        >
          <Icon name="plus" size={11} /> {t("rp.new")}
        </button>
      </PageToolbar>

      {view === "list" ? (
        <ReportsSection {...{ t, selectedId, setSelectedId, selected, setDrawer }} />
      ) : (
        <ReportShelf
          onOpen={(id) => {
            setSelectedId(id);
            setView("list");
          }}
        />
      )}

      <ReportsDetailsDrawer {...{ drawer, setDrawer, t }} />
    </div>
  );
};
