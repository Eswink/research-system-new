import { useState, type Dispatch, type SetStateAction } from "react";
import FIX_EXPERIMENT_QUEUE from "../data/experiment-queue.json";
import { requiredExample } from "../requiredExample";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Drawer } from "./Drawer";
import { ExperimentCalendar } from "./ExperimentCalendar";
import { ExperimentDetail } from "./ExperimentDetail";
import { ExperimentForm } from "./ExperimentForm";
import { ExperimentMatrix } from "./ExperimentMatrix";
import { ExperimentQueue } from "./ExperimentQueue";
import visual from "./ExperimentsScreen.module.css";
import { Icon } from "./Icon";
import { PageToolbar } from "./PageToolbar";
import { SearchInput } from "./SearchInput";
import { ViewSwitcher } from "./ViewSwitcher";

/** Reference: screens/Experiments.jsx; EXAMPLE ONLY. */
export const ExperimentsScreen = () => {
  const { t } = useI18n();
  const [view, setView] = useState("queue");
  const [selectedId, setSelectedId] = useState(requiredExample(FIX_EXPERIMENT_QUEUE[0]).id);
  const [drawer, setDrawer] = useState<{ mode?: string } | null>(null);
  const [q, setQ] = useState("");
  const selected = FIX_EXPERIMENT_QUEUE.find((e) => e.id === selectedId);

  return (
    <div className={visual.column}>
      <PageToolbar title={t("exp.title")} subtitle={t("exp.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("exp.search")} width={220} />
        <ViewSwitcher
          value={view}
          onChange={setView}
          views={[
            { value: "queue", label: t("exp.viewQueue"), icon: "menu" },
            { value: "matrix", label: t("exp.viewMatrix"), icon: "square" },
            { value: "calendar", label: t("exp.viewCalendar"), icon: "clock" },
          ]}
        />
        <button
          className="btn primary sm"
          onClick={() => {
            setDrawer({ mode: "create" });
          }}
        >
          <Icon name="plus" size={11} /> {t("exp.new")}
        </button>
      </PageToolbar>

      {view === "queue" && (
        <div className={visual.grid}>
          <ExperimentQueue
            queue={FIX_EXPERIMENT_QUEUE}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
          <ExperimentDetail experiment={requiredExample(selected)} />
        </div>
      )}
      {view === "matrix" && <ExperimentMatrix experiments={FIX_EXPERIMENT_QUEUE} />}
      {view === "calendar" && <ExperimentCalendar experiments={FIX_EXPERIMENT_QUEUE} />}

      <ExperimentsNew {...{ drawer, setDrawer, t }} />
    </div>
  );
};

interface ExperimentsNewProps {
  drawer: { mode?: string } | null;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
  t: (key: string, fallback?: string) => string;
}

function ExperimentsNew({ drawer, setDrawer, t }: ExperimentsNewProps) {
  return (
    <Drawer
      open={!!drawer}
      onClose={() => {
        setDrawer(null);
      }}
      title={t("exp.new")}
      subtitle={t("exp.newSub")}
      width={560}
      footer={
        <>
          <button
            className="btn ghost"
            onClick={() => {
              setDrawer(null);
            }}
          >
            {t("act.cancel")}
          </button>
          <div className={visual.label}>
            <span className="mono">{t("exp.totalRuns")}</span>{" "}
            <strong className={visual.surface}>96</strong>
          </div>
          <button
            className="btn primary"
            onClick={() => {
              setDrawer(null);
            }}
          >
            <Icon name="play" size={11} /> {t("exp.queueRun")}
          </button>
        </>
      }
    >
      <ExperimentForm />
    </Drawer>
  );
}
