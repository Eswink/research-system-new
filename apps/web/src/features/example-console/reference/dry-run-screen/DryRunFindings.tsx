import { type Dispatch, type SetStateAction } from "react";
import visual from "../DryRunScreen.module.css";
import type { ExamplePreflight } from "../preflightModel";
import { DryRunFindings2 } from "./DryRunFindings2";
import { DryRunSection } from "./DryRunSection";

interface DryRunFindingsProps {
  preflight: ExamplePreflight;
  t: (key: string, fallback?: string) => string;
  warnCount: number;
  infoCount: number;
  errorCount: number;
  canStart: boolean;
  ack: boolean;
  setAck: Dispatch<SetStateAction<boolean>>;
  selectedFinding: number;
  setSelectedFinding: Dispatch<SetStateAction<number>>;
}

export function DryRunFindings({
  preflight,
  t,
  warnCount,
  infoCount,
  errorCount,
  canStart,
  ack,
  setAck,
  selectedFinding,
  setSelectedFinding,
}: DryRunFindingsProps) {
  return (
    <div className={visual.column}>
      {/* Status bar — P1: Start disabled unless clean or warnings acknowledged */}
      <DryRunSection
        {...{ preflight, t, warnCount, infoCount, errorCount, canStart, ack, setAck }}
      />

      {/* Scrollable body — 5 zones */}
      <DryRunFindings2
        {...{ t, preflight, errorCount, warnCount, infoCount, selectedFinding, setSelectedFinding }}
      />
    </div>
  );
}
