import { useState } from "react";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./DryRunScreen.module.css";
import { ProtocolEditor } from "./ProtocolEditor";
import {
  canStartPreflight,
  examplePreflight,
  preflightCounts,
  type ExamplePreflightKind,
} from "./preflightModel";
import { DryRunFindings } from "./dry-run-screen/DryRunFindings";

export const DryRunScreen = ({
  preflightState = "warn",
  protocolMode = "form",
  protocolErrorLevel = "some",
  protocolLanguages = 7,
  protocolTemperatures = 6,
  protocolAdminMode = false,
}: {
  preflightState?: ExamplePreflightKind;
  protocolMode?: string;
  protocolErrorLevel?: string;
  protocolLanguages?: number;
  protocolTemperatures?: number;
  protocolAdminMode?: boolean;
}) => {
  const { t } = useI18n();
  const preflight = examplePreflight(preflightState);
  const [selectedFinding, setSelectedFinding] = useState(0);
  const [ack, setAck] = useState(false);
  const canStart = canStartPreflight(preflight, ack);
  const { errorCount, warnCount, infoCount } = preflightCounts(preflight);
  return (
    <div className={visual.grid}>
      {/* ── Left: Protocol Editor (Form ↔ YAML) ─────────── */}
      <ProtocolEditor
        mode={protocolMode}
        errorLevel={protocolErrorLevel}
        adminMode={protocolAdminMode}
        languagesCount={protocolLanguages}
        temperatureCount={protocolTemperatures}
      />

      {/* ── Right: Preflight report ─────────────────────── */}
      <DryRunFindings
        {...{
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
        }}
      />
    </div>
  );
};
