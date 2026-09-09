import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../CompareScreen.module.css";
import { Icon } from "../Icon";
import { PageToolbar } from "../PageToolbar";

interface CompareTitleProps {
  t: (key: string, fallback?: string) => string;
  hideUnchanged: boolean;
  setHideUnchanged: Dispatch<SetStateAction<boolean>>;
  setPickerOpen: Dispatch<SetStateAction<boolean>>;
  selectedRuns: FixtureTypes.Run[];
}

export function CompareTitle({
  t,
  hideUnchanged,
  setHideUnchanged,
  setPickerOpen,
  selectedRuns,
}: CompareTitleProps) {
  return (
    <PageToolbar title={t("cmp.title")} subtitle={t("cmp.subtitle")}>
      <label className={visual.row}>
        <input
          type="checkbox"
          checked={hideUnchanged}
          onChange={(e) => {
            setHideUnchanged(e.target.checked);
          }}
        />
        {t("cmp.hideUnchanged")}
      </label>
      <button
        className="btn sm"
        onClick={() => {
          setPickerOpen(true);
        }}
      >
        <Icon name="plus" size={11} /> {t("cmp.pickRuns")} ({selectedRuns.length}/4)
      </button>
      <button className="btn primary sm">
        <Icon name="external" size={11} /> {t("cmp.exportDiff")}
      </button>
    </PageToolbar>
  );
}
