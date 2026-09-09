import { useState, type Dispatch, type SetStateAction } from "react";
import FIX_CLAIMS from "../data/claims.json";
import FIX_EVIDENCE from "../data/evidence.json";
import { requiredExample } from "../requiredExample";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { ClaimDetail } from "./ClaimDetail";
import { ClaimsGraph } from "./ClaimsGraph";
import visual from "./ClaimsScreen.module.css";
import { ClaimsTable } from "./ClaimsTable";
import { Icon } from "./Icon";

/** Reference: screens/Claims.jsx; EXAMPLE ONLY. */
export const ClaimsScreen = ({ initialView = "graph" }: { initialView?: string }) => {
  const { t } = useI18n();
  const [view, setView] = useState(initialView);
  // Start on the disputed example because it exposes the full evidence state.
  const [selectedClaimId, setSelectedClaimId] = useState("clm_h3_opus_stable");
  const [filter, setFilter] = useState("all");

  const filteredClaims =
    filter === "all" ? FIX_CLAIMS : FIX_CLAIMS.filter((c) => c.status === filter);
  const selectedClaim = FIX_CLAIMS.find((c) => c.id === selectedClaimId);

  return (
    <div className={visual.grid}>
      <div className={`panel ${visual.panel ?? ""}`}>
        {/* Toolbar */}
        <ClaimsSection {...{ t, setView, view, setFilter, filter }} />

        {/* View content */}
        <div className={visual.surface3}>
          {view === "graph" ? (
            <ClaimsGraph
              claims={filteredClaims}
              selectedId={selectedClaimId}
              onSelect={setSelectedClaimId}
            />
          ) : (
            <ClaimsTable
              claims={filteredClaims}
              selectedId={selectedClaimId}
              onSelect={setSelectedClaimId}
            />
          )}
        </div>
      </div>

      {/* Right rail: claim detail */}
      <ClaimDetail claim={requiredExample(selectedClaim)} />
    </div>
  );
};

interface ClaimsSectionProps {
  t: (key: string, fallback?: string) => string;
  setView: Dispatch<SetStateAction<string>>;
  view: string;
  setFilter: Dispatch<SetStateAction<string>>;
  filter: string;
}

function ClaimsSection({ t, setView, view, setFilter, filter }: ClaimsSectionProps) {
  return (
    <div className={visual.row}>
      <div className={visual.row2}>
        {(
          [
            ["graph", t("tw.claimsGraph"), "graph"],
            ["table", t("tw.claimsTable"), "menu"],
          ] as const
        ).map(([v, l, icn]) => (
          <button
            key={v}
            onClick={() => {
              setView(v);
            }}
            className="btn sm ghost"
            style={{
              background: view === v ? "var(--bg-hover)" : "transparent",
              color: view === v ? "var(--fg)" : "var(--fg-muted)",
              fontWeight: view === v ? 500 : 400,
              border: view === v ? "1px solid var(--border-strong)" : "1px solid transparent",
            }}
          >
            <Icon name={icn} size={10} /> {l}
          </button>
        ))}
      </div>
      <div className={`vr ${visual.surface ?? ""}`} />
      <ClaimsSection2 {...{ setFilter, filter }} />
      <span className={visual.label}>
        {FIX_EVIDENCE.length} {t("cl.evidence")}{" "}
        {new Set(FIX_EVIDENCE.map((e) => e.source_ref)).size} {t("cl.sources")}
      </span>
    </div>
  );
}

interface ClaimsSection2Props {
  setFilter: Dispatch<SetStateAction<string>>;
  filter: string;
}

function ClaimsSection2({ setFilter, filter }: ClaimsSection2Props) {
  return (
    <div className={visual.row3}>
      {(
        [
          ["all", FIX_CLAIMS.length],
          ["VERIFIED", FIX_CLAIMS.filter((c) => c.status === "VERIFIED").length],
          ["PROPOSED", FIX_CLAIMS.filter((c) => c.status === "PROPOSED").length],
          ["DISPUTED", FIX_CLAIMS.filter((c) => c.status === "DISPUTED").length],
          ["REFUTED", FIX_CLAIMS.filter((c) => c.status === "REFUTED").length],
        ] as const
      ).map(([s, n]) => (
        <button
          key={s}
          onClick={() => {
            setFilter(s);
          }}
          className={`btn sm ghost ${visual.action ?? ""}`}
          style={{
            background: filter === s ? "var(--bg-hover)" : "transparent",
            color: filter === s ? "var(--fg)" : "var(--fg-muted)",
          }}
        >
          {s.toLowerCase()} <span className={visual.surface2}>{n}</span>
        </button>
      ))}
    </div>
  );
}
