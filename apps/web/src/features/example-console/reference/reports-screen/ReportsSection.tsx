import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import type * as FixtureTypes from "../../fixtureTypes";
import { ReportPreview } from "../ReportPreview";
import visual from "../ReportsScreen.module.css";
import { ReportsSection2 } from "./ReportsSection2";

interface ReportsSectionProps {
  t: (key: string, fallback?: string) => string;
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
  selected: FixtureTypes.Report | undefined;
  setDrawer: Dispatch<SetStateAction<E.ReportDrawer | null>>;
}

export function ReportsSection({
  t,
  selectedId,
  setSelectedId,
  selected,
  setDrawer,
}: ReportsSectionProps) {
  return (
    <div className={visual.grid}>
      <ReportsSection2 {...{ t, selectedId, setSelectedId }} />

      {selected && (
        <ReportPreview
          report={selected}
          onEdit={() => {
            setDrawer({ mode: "edit", report: selected });
          }}
        />
      )}
    </div>
  );
}
