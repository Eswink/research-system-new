import { useState, type Dispatch, type SetStateAction } from "react";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import visual from "./QuickCreate.module.css";

/** Reference: components/patterns.jsx; EXAMPLE ONLY. */
export const QuickCreate = ({ onCreate }: { onCreate: (type: string) => void }) => {
  const [open, setOpen] = useState(false);
  // useI18n falls back to identity when there's no provider — safe to call
  // unconditionally so this component works standalone (e.g. in Command Center).
  const { t } = useI18n();
  const opts = [
    { id: "project", label: t("qc.newProject", "New Project"), icon: "hex", shortcut: "P" },
    {
      id: "experiment",
      label: t("qc.newExperiment", "New Experiment"),
      icon: "flask",
      shortcut: "E",
    },
    { id: "prompt", label: t("qc.newPrompt", "New Prompt"), icon: "book", shortcut: "R" },
    { id: "notebook", label: t("qc.newNotebook", "New Notebook"), icon: "book", shortcut: "N" },
    { id: "alert", label: t("qc.newAlert", "New Alert Rule"), icon: "warn-tri", shortcut: "A" },
    { id: "schedule", label: t("qc.newSchedule", "New Schedule"), icon: "clock", shortcut: "S" },
  ];
  return <QuickCreateSurface {...{ setOpen, open, t, opts, onCreate }} />;
};

interface QuickCreateSurfaceProps {
  setOpen: Dispatch<SetStateAction<boolean>>;
  open: boolean;
  t: (key: string, fallback?: string) => string;
  opts: { id: string; label: string; icon: string; shortcut: string }[];
  onCreate: (type: string) => void;
}

function QuickCreateSurface({ setOpen, open, t, opts, onCreate }: QuickCreateSurfaceProps) {
  return (
    <div className={visual.surface}>
      <button
        className="btn sm primary"
        onClick={() => {
          setOpen(!open);
        }}
      >
        <Icon name="plus" size={11} /> {t("act.create", "Create")}
      </button>
      {open && (
        <>
          <div
            className={visual.overlay}
            onClick={() => {
              setOpen(false);
            }}
          />
          <div className={visual.overlay2}>
            {opts.map((o) => (
              <button
                key={o.id}
                onClick={() => {
                  onCreate(o.id);
                  setOpen(false);
                }}
                className={visual.row}
                onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-hover)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
              >
                <Icon name={o.icon} size={11} className={visual.surface2} />
                <span className={visual.surface3}>{o.label}</span>
                <kbd>{o.shortcut}</kbd>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
