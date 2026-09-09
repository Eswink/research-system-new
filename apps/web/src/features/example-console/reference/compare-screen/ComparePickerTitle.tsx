import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../CompareScreen.module.css";
import { Drawer } from "../Drawer";
import { CompareSection9 } from "./CompareSection9";

interface ComparePickerTitleProps {
  pickerOpen: boolean;
  setPickerOpen: Dispatch<SetStateAction<boolean>>;
  t: (key: string, fallback?: string) => string;
  allRuns: FixtureTypes.Run[];
  selected: string[];
  toggleRun: (id: string) => void;
}

export function ComparePickerTitle({
  pickerOpen,
  setPickerOpen,
  t,
  allRuns,
  selected,
  toggleRun,
}: ComparePickerTitleProps) {
  return (
    <Drawer
      open={pickerOpen}
      onClose={() => {
        setPickerOpen(false);
      }}
      title={t("cmp.pickerTitle")}
      subtitle={t("cmp.pickerSub")}
      width={520}
    >
      <div className={visual.label9}>{t("cmp.pickerHint")}</div>
      <CompareSection9 {...{ allRuns, selected, toggleRun }} />
    </Drawer>
  );
}
