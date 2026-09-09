import type * as E from "../exampleTypes";
import { StatusBadge } from "./StatusBadge";

/** Reference: screens/Prompts.jsx; EXAMPLE ONLY. */
export const PromptStatusBadge = ({ status }: { status: string }) => {
  const map: Record<string, E.BadgeProps> = {
    PRODUCTION: { tone: "success", icon: "check", label: "PROD", filled: true },
    STAGING: { tone: "warn", icon: "flask", label: "STAGING", filled: true },
    DRAFT: { tone: "neutral", icon: "circle-o", label: "DRAFT", dashed: true },
  };
  return <StatusBadge {...(map[status] ?? { tone: "unknown", label: status })} />;
};
