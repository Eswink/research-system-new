import { useState, type Dispatch, type SetStateAction } from "react";
import visual from "../DryRunScreen.module.css";
import { Icon } from "../Icon";
import { isBlocked, isReady, type ExamplePreflight } from "../preflightModel";

interface DryRunSection3Props {
  canStart: boolean;
  t: (key: string, fallback?: string) => string;
  preflight: ExamplePreflight;
  ack: boolean;
  setAck: Dispatch<SetStateAction<boolean>>;
  warnCount: number;
  errorCount: number;
}

export function DryRunSection3({
  canStart,
  t,
  preflight,
  ack,
  setAck,
  warnCount,
  errorCount,
}: DryRunSection3Props) {
  const warning = !isReady(preflight) && !isBlocked(preflight);
  return (
    <div className={visual.column2}>
      <StartGateButton {...{ canStart, t }} />
      {warning && <AckGateCheckbox {...{ ack, setAck, warnCount, t }} />}
      {isBlocked(preflight) && (
        <span className={visual.row4}>
          <Icon name="lock" size={10} /> {t("dr.blockedBy")} {errorCount} {t("dr.blockedBy2")}
          {errorCount > 1 ? "s" : ""}
        </span>
      )}
    </div>
  );
}

interface GateChildProps {
  t: (key: string, fallback?: string) => string;
}

function StartGateButton({ canStart, t }: GateChildProps & { canStart: boolean }) {
  const [gateDemoed, setGateDemoed] = useState(false);
  return (
    <>
      <button
        className={`btn primary ${visual.action ?? ""}`}
        disabled={!canStart}
        aria-disabled={!canStart}
        title={canStart ? t("dr.startTip.ok") : t("dr.startTip.blocked")}
        onClick={() => {
          setGateDemoed(true);
        }}
      >
        <Icon name="play" size={11} /> {t("dr.startRun")}
      </button>
      {gateDemoed && (
        <span className={visual.row4} data-testid="example-start-note" role="status">
          {t("dr.startDemo", "Example gate only — no real run was started")}
        </span>
      )}
    </>
  );
}

function AckGateCheckbox({
  ack,
  setAck,
  warnCount,
  t,
}: GateChildProps & {
  ack: boolean;
  setAck: Dispatch<SetStateAction<boolean>>;
  warnCount: number;
}) {
  return (
    <label className={visual.row3}>
      <input
        type="checkbox"
        checked={ack}
        onChange={(e) => {
          setAck(e.target.checked);
        }}
        className={visual.field}
      />
      {t("dr.ackI")} {warnCount} {t("dr.ackWarn")}
      {warnCount > 1 ? "s" : ""}
    </label>
  );
}
