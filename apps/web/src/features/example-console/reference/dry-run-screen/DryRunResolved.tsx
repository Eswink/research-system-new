import FIX_AGENTS from "../../data/agents.json";
import FIX_ROLES from "../../data/roles.json";
import visual from "../DryRunScreen.module.css";
import { ZoneHeader } from "../ZoneHeader";

interface DryRunResolvedProps {
  t: (key: string, fallback?: string) => string;
}

export function DryRunResolved({ t }: DryRunResolvedProps) {
  const activeRoleCount = FIX_ROLES.filter((role) => role.active > 0).length;
  const inactiveRoleCount = FIX_ROLES.filter((role) => role.active === 0).length;
  return (
    <section className="panel">
      <ZoneHeader
        icon="hex"
        title={t("dr.resolved")}
        count={activeRoleCount}
        extra={
          <span className={visual.label4}>
            {FIX_AGENTS.length} {t("dr.agents")} {inactiveRoleCount} {t("dr.collapsed")}
          </span>
        }
      />
      <div className={visual.grid2}>
        {FIX_ROLES.map((r) => (
          <div
            key={r.id}
            className={visual.row5}
            style={{
              background: r.active === 0 ? "transparent" : "var(--bg-raised)",
              border: `1px ${r.active === 0 ? "dashed" : "solid"} var(--border)`,
              opacity: r.active === 0 ? 0.55 : 1,
            }}
          >
            <div className={visual.surface8}>
              <div
                className={visual.label5}
                style={{ color: r.active === 0 ? "var(--fg-faint)" : "var(--fg)" }}
              >
                {r.name}
              </div>
              {r.collapsed_reason && (
                <div className={visual.caption}>
                  {t("tm.rolesCollapsed")} {r.collapsed_reason}
                </div>
              )}
            </div>
            <span className={`chip ${visual.surface9 ?? ""}`}>
              {r.active}/{r.max}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
