import { useState, type Dispatch, type SetStateAction } from "react";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import visual from "./WorkspaceSwitcher.module.css";

/** Reference: components/patterns.jsx; EXAMPLE ONLY. */
export const WorkspaceSwitcher = ({ workspaces }: { workspaces: E.Workspace[] }) => {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const cur = workspaces.find((w) => w.current) ?? workspaces[0];
  return (
    <div className={visual.surface}>
      <button
        onClick={() => {
          setOpen(!open);
        }}
        className={visual.row}
      >
        <div className={visual.indicator} />
        <span className={visual.surface2}>{cur?.name ?? "Example workspace"}</span>
        <Icon name="chevron-d" size={9} className={visual.surface3} />
      </button>
      {open && (
        <>
          <div
            className={visual.overlay}
            onClick={() => {
              setOpen(false);
            }}
          />
          <WorkspaceSwitcherCaption {...{ t, workspaces, setOpen }} />
        </>
      )}
    </div>
  );
};

interface WorkspaceSwitcherCaptionProps {
  t: (key: string, fallback?: string) => string;
  workspaces: {
    id: string;
    name: string;
    role: string;
    members: number;
    plan: string;
    current: boolean;
  }[];
  setOpen: Dispatch<SetStateAction<boolean>>;
}

function WorkspaceSwitcherCaption({ t, workspaces, setOpen }: WorkspaceSwitcherCaptionProps) {
  return (
    <div className={visual.overlay2}>
      <div className={visual.caption}>{t("ws2.workspaces", "Workspaces")}</div>
      {workspaces.map((w) => (
        <button
          key={w.id}
          onClick={() => {
            setOpen(false);
          }}
          className={visual.row2}
        >
          <div className={visual.indicator2} />
          <div className={visual.surface4}>
            <div className={visual.surface5}>{w.name}</div>
            <div className={visual.caption2}>
              {w.role} · {w.members} · {w.plan}
            </div>
          </div>
          {w.current && <Icon name="check" size={11} className={visual.surface6} />}
        </button>
      ))}
      <div className={visual.surface7}>
        <button className={`btn sm ghost ${visual.action ?? ""}`}>
          <Icon name="plus" size={10} /> {t("ws2.new", "New workspace")}
        </button>
      </div>
    </div>
  );
}
