import FIX_ROLES from "../../data/roles.json";
import { Icon } from "../Icon";
import visual from "../TeamScreen.module.css";

interface TeamSection8Props {
  t: (key: string, fallback?: string) => string;
}

export function TeamSection8({ t }: TeamSection8Props) {
  return (
    <div className={visual.surface3}>
      {FIX_ROLES.map((r) => (
        <div key={r.id} className={visual.surface4} style={{ opacity: r.active === 0 ? 0.55 : 1 }}>
          <div className={visual.row3}>
            <Icon
              name={r.active === 0 ? "circle-dash" : "circle"}
              size={10}
              style={{ color: r.active === 0 ? "var(--fg-faint)" : "var(--accent)" }}
            />
            <span
              className={visual.label4}
              style={{ color: r.active === 0 ? "var(--fg-faint)" : "var(--fg)" }}
            >
              {r.name}
            </span>
            <span className={`chip ${visual.surface5 ?? ""}`}>
              {r.active}/{r.max}
            </span>
          </div>
          {r.collapsed_reason && (
            <div className={visual.caption2}>
              {t("tm.rolesCollapsed")} {r.collapsed_reason}
            </div>
          )}
          <div className={visual.row4}>
            {r.capabilities.slice(0, 4).map((c) => (
              <span key={c} className={visual.row5}>
                {c}
              </span>
            ))}
            {r.forbidden.map((c) => (
              <span key={c} title="forbidden capability" className={visual.row6}>
                <Icon name="ban" size={8} className={visual.surface6} />
                {c}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
