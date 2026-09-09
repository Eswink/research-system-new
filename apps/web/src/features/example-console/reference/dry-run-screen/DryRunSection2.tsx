import { type Dispatch, type SetStateAction } from "react";
import { DigestText } from "../DigestText";
import visual from "../DryRunScreen.module.css";
import { PreflightBadge } from "../PreflightBadge";
import { isBlocked, isReady, type ExamplePreflight } from "../preflightModel";
import { DryRunSection3 } from "./DryRunSection3";

interface DryRunSection2Props {
  preflight: ExamplePreflight;
  t: (key: string, fallback?: string) => string;
  warnCount: number;
  infoCount: number;
  errorCount: number;
  canStart: boolean;
  ack: boolean;
  setAck: Dispatch<SetStateAction<boolean>>;
}

function readySummary(
  preflight: ExamplePreflight,
  t: DryRunSection2Props["t"],
  { warnCount, infoCount, errorCount }: DryRunSection2Props,
): string {
  if (isBlocked(preflight))
    return t("dr.readyFail")
      .replace("{n}", String(errorCount))
      .replace("{s}", errorCount > 1 ? "s" : "")
      .replace("{w}", String(warnCount));
  if (isReady(preflight)) return t("dr.readyPass");
  return t("dr.readyWarn")
    .replace("{n}", String(warnCount))
    .replace("{s}", warnCount > 1 ? "s" : "")
    .replace("{i}", String(infoCount));
}

export function DryRunSection2(props: DryRunSection2Props) {
  const { preflight, t, canStart, ack, setAck, warnCount, errorCount } = props;
  const compiledSummary = [
    t("dr.compiledAt"),
    "2026-08-27T14:02:18Z",
    "· plan_id plan_01K5FZ8G3X2 ·",
    t("dr.elapsed"),
    "2.4s",
  ].join(" ");
  return (
    <div className={visual.row}>
      <div className={visual.surface}>
        <div className={visual.row2}>
          <PreflightBadge status={preflight.status} />
          <span className={visual.label}>{t("dr.report")}</span>
          <DigestText
            value="sha256:preflight_a9c4e21f0b8d47bf12e6c3a9"
            label="report:"
            length={8}
          />
        </div>
        <div className={visual.label2}>{readySummary(preflight, t, props)}</div>
        <div className={visual.label3}>{compiledSummary}</div>
      </div>

      <DryRunSection3 {...{ canStart, t, preflight, ack, setAck, warnCount, errorCount }} />
    </div>
  );
}
