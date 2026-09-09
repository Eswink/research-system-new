import type * as E from "../exampleTypes";
import { StatusBadge } from "./StatusBadge";

/** Reference: screens/Reports.jsx; EXAMPLE ONLY. */
export const ReportStatusBadge = ({ status }: { status: string }) => {
  const map: Record<string, E.BadgeProps> = {
    DRAFT: { tone: "neutral", icon: "circle-o", label: "DRAFT", dashed: true },
    IN_REVIEW: { tone: "warn", icon: "eye-off", label: "IN REVIEW", filled: true },
    PUBLISHED: { tone: "success", icon: "check", label: "PUBLISHED", filled: true },
  };
  return <StatusBadge {...(map[status] ?? { tone: "unknown", label: status })} />;
};
