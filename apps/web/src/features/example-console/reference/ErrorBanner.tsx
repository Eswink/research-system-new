import { useState, type Dispatch, type SetStateAction } from "react";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./ErrorBanner.module.css";
import { Icon } from "./Icon";

/** Reference: screens/ProtocolEditor.parts.jsx; EXAMPLE ONLY. */
export const ErrorBanner = ({
  errors,
  onJump,
}: {
  errors: E.ProtocolIssue[];
  onJump: (section: string) => void;
}) => {
  const { t } = useI18n();
  const [expanded, setExpanded] = useState(false);
  return <ErrorBannerSurface {...{ errors, t, setExpanded, expanded, onJump }} />;
};

interface ErrorBannerSurfaceProps {
  errors: E.ProtocolIssue[];
  t: (key: string, fallback?: string) => string;
  setExpanded: Dispatch<SetStateAction<boolean>>;
  expanded: boolean;
  onJump: (section: string) => void;
}

function ErrorBannerSurface({ errors, t, setExpanded, expanded, onJump }: ErrorBannerSurfaceProps) {
  return (
    <div className={visual.surface}>
      <div className={visual.row}>
        <Icon name="x" size={11} className={visual.surface2} />
        <span>
          <strong className={visual.surface3}>
            {errors.length} {t("pe.err.block")}
          </strong>{" "}
          {t("pe.err.msg")}
        </span>
        <button
          className={`btn sm ghost ${visual.action ?? ""}`}
          onClick={() => {
            setExpanded((v) => !v);
          }}
        >
          {expanded ? t("pe.err.collapse") : t("pe.err.expand")}
          <Icon name={expanded ? "chevron-d" : "chevron-r"} size={9} />
        </button>
      </div>
      {expanded && (
        <div className={visual.column}>
          {errors.map((e, i) => (
            <button
              key={i}
              onClick={() => {
                onJump(e.section);
              }}
              className={`btn sm ghost ${visual.action2 ?? ""}`}
            >
              <span className={`mono ${visual.surface4 ?? ""}`}>{e.code}</span>
              <span className={visual.surface5}>·</span>
              <span className={`mono ${visual.caption ?? ""}`}>{e.path}</span>
              <span className={visual.surface6}>·</span>
              <span>{e.message}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
