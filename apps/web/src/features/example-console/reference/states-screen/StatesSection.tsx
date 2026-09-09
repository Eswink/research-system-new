import type { JSX } from "react/jsx-runtime";
import visual from "../StatesScreen.module.css";
import { StatusBadge } from "../StatusBadge";

interface StatesSectionProps {
  t: (key: string, fallback?: string) => string;
  states: {
    id: string;
    tone: string;
    icon: string;
    title: string;
    desc: string;
    demo: JSX.Element;
  }[];
}

export function StatesSection({ t, states }: StatesSectionProps) {
  return (
    <div className={visual.surface19}>
      <div className={visual.surface20}>
        <div className={visual.caption}>{t("sm.contract")}</div>
        <div className={visual.label10}>{t("sm.title")}</div>
        <div className={visual.label11}>{t("sm.desc")}</div>
      </div>
      <div className={visual.grid2}>
        {states.map((s) => (
          <div key={s.id} className={`panel ${visual.panel ?? ""}`}>
            <div className={visual.row4}>
              <StatusBadge
                tone={s.tone === "info" ? "neutral" : s.tone}
                icon={s.icon}
                label={s.title}
                size="sm"
                filled
              />
              <span className={visual.label12}>{s.desc}</span>
            </div>
            <div>{s.demo}</div>
          </div>
        ))}
      </div>
      <style>
        {[
          "\n        @keyframes shimmer {\n          0%, 100% { opacity: 0.5; }\n      ",
          "    50%      { opacity: 1; }\n        }\n      ",
        ].join("")}
      </style>
    </div>
  );
}
