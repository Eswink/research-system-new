import visual from "../DryRunScreen.module.css";
import { ZoneHeader } from "../ZoneHeader";
import type { ExamplePreflight } from "../preflightModel";

interface DryRunFindings4Props {
  t: (key: string, fallback?: string) => string;
  preflight: ExamplePreflight;
  errorCount: number;
  warnCount: number;
  infoCount: number;
}

export function DryRunFindings4({
  t,
  preflight,
  errorCount,
  warnCount,
  infoCount,
}: DryRunFindings4Props) {
  return (
    <ZoneHeader
      icon="warn-tri"
      title={t("dr.findings")}
      count={preflight.findings.length}
      extra={
        <>
          <span className={`chip ${visual.surface2 ?? ""}`}>
            {errorCount} {t("dr.fErr")}
          </span>
          <span className={`chip ${visual.surface3 ?? ""}`}>
            {warnCount} {t("dr.fWarn")}
          </span>
          <span className={`chip ${visual.surface4 ?? ""}`}>
            {infoCount} {t("dr.fInfo")}
          </span>
        </>
      }
    />
  );
}
