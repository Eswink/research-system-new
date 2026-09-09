import { Icon } from "./Icon";
import visual from "./ReproducibilityChip.module.css";

/** Reference: components/atoms.jsx; EXAMPLE ONLY. */
export const ReproducibilityChip = ({
  fingerprint,
  providerAvailable,
  compact = false,
}: {
  fingerprint?: string | null | undefined;
  providerAvailable?: boolean | null | undefined;
  compact?: boolean;
}) => {
  // Hard rule from DTO: provider_fingerprint_available=false → unknown
  if (providerAvailable === false || !fingerprint) {
    return (
      <span
        title="Configuration reproducible / provider fingerprint unavailable"
        className={visual.row}
      >
        <Icon name="q" size={10} />
        {compact ? "CFG-ONLY" : "Configuration reproducible"}
      </span>
    );
  }
  return (
    <span title={`Fully reproducible · fingerprint ${fingerprint}`} className={visual.row2}>
      <Icon name="check" size={10} />
      {compact ? "REPRODUCIBLE" : "Fully reproducible"}
    </span>
  );
};
