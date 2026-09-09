import type * as E from "../exampleTypes";
import { StatusBadge } from "./StatusBadge";

/** Reference: components/atoms.jsx; EXAMPLE ONLY. */
export const ClaimStatusBadge = ({ status }: { status: string }) => {
  const map: Record<string, E.BadgeProps> = {
    PROPOSED: { tone: "neutral", icon: "circle-dash", label: "PROPOSED", dashed: true },
    VERIFIED: { tone: "success", icon: "check", label: "VERIFIED", filled: true },
    DISPUTED: { tone: "warn", icon: "warn-tri", label: "DISPUTED", filled: true },
    REFUTED: { tone: "danger", icon: "x", label: "REFUTED", filled: true },
  };
  return <StatusBadge {...map[status]} />;
};
