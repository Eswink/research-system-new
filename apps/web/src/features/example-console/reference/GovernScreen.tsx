import { useState } from "react";
import FIX_AUDIT from "../data/audit.json";
import FIX_MEMORY from "../data/memory.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { AuditTab } from "./AuditTab";
import { ExportTab } from "./ExportTab";
import visual from "./GovernScreen.module.css";
import { Icon } from "./Icon";
import { MemoryTab } from "./MemoryTab";

/** Reference: screens/Govern.jsx; EXAMPLE ONLY. */
export const GovernScreen = () => {
  const { t } = useI18n();
  const [tab, setTab] = useState("audit");

  return (
    <div className={visual.column}>
      <div className={`panel ${visual.panel ?? ""}`}>
        <div className={visual.row}>
          {(
            [
              ["audit", t("gv.audit"), "menu", FIX_AUDIT.length],
              ["export", t("gv.export"), "external", 1],
              ["memory", t("gv.memory"), "book", FIX_MEMORY.length],
            ] as const
          ).map(([id, label, icn, count]) => (
            <button
              key={id}
              onClick={() => {
                setTab(id);
              }}
              className="btn ghost"
              style={{
                background: tab === id ? "var(--bg-hover)" : "transparent",
                color: tab === id ? "var(--fg)" : "var(--fg-muted)",
                border: `1px solid ${tab === id ? "var(--border-strong)" : "transparent"}`,
                fontWeight: tab === id ? 500 : 400,
              }}
            >
              <Icon name={icn} size={11} /> {label}
              <span className={`chip ${visual.surface ?? ""}`}>{count}</span>
            </button>
          ))}
        </div>
      </div>

      <div className={visual.surface2}>
        {tab === "audit" && <AuditTab />}
        {tab === "export" && <ExportTab />}
        {tab === "memory" && <MemoryTab />}
      </div>
    </div>
  );
};
