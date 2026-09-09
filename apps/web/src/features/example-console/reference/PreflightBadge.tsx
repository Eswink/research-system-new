import type * as E from "../exampleTypes";
import { preflightToneByStatus } from "./preflightModel";
import { StatusBadge } from "./StatusBadge";

/** Reference: components/atoms.jsx; EXAMPLE ONLY. Tone derives from fixture severities. */
export const PreflightBadge = ({ status }: { status: string }) => {
  const tone = preflightToneByStatus(status);
  const icon = tone === "success" ? "check" : tone === "danger" ? "x" : "warn-tri";
  const badge: E.BadgeProps = { tone, icon, label: status, filled: true };
  return <StatusBadge {...badge} />;
};
