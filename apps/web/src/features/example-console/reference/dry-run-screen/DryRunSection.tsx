import { type Dispatch, type SetStateAction } from "react";
import visual from "../DryRunScreen.module.css";
import { isBlocked, isReady } from "../preflightModel";
import { DryRunSection2 } from "./DryRunSection2";
import type { ExamplePreflight } from "../preflightModel";

interface DryRunSectionProps {
  preflight: ExamplePreflight;
  t: (key: string, fallback?: string) => string;
  warnCount: number;
  infoCount: number;
  errorCount: number;
  canStart: boolean;
  ack: boolean;
  setAck: Dispatch<SetStateAction<boolean>>;
}

const BORDER: Readonly<Record<string, string>> = {
  blocked: "var(--danger-line)",
  warning: "var(--warn-line)",
  ready: "var(--success-line)",
};
const BACKGROUND: Readonly<Record<string, string>> = {
  blocked: "linear-gradient(180deg, var(--danger-dim), transparent 60%)",
  warning: "linear-gradient(180deg, var(--warn-dim), transparent 60%)",
  ready: "linear-gradient(180deg, var(--success-dim), transparent 60%)",
};

function reportState(preflight: ExamplePreflight): keyof typeof BORDER {
  if (isBlocked(preflight)) return "blocked";
  return isReady(preflight) ? "ready" : "warning";
}

export function DryRunSection({
  preflight,
  t,
  warnCount,
  infoCount,
  errorCount,
  canStart,
  ack,
  setAck,
}: DryRunSectionProps) {
  const state = reportState(preflight);
  return (
    <div
      className={`panel ${visual.panel ?? ""}`}
      style={{ borderColor: BORDER[state], background: BACKGROUND[state] }}
    >
      <DryRunSection2
        {...{ preflight, t, warnCount, infoCount, errorCount, canStart, ack, setAck }}
      />
    </div>
  );
}
