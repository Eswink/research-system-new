import { useEffect, useState } from "react";
import type { ConsoleProps } from "../../../layout/consoleProps";
import { SourceControl } from "../../../layout/SourceControl";
import { DEFAULT_ROUTE } from "../../../navigation/registry";
import "./command-center.css";
import { CommandCenter } from "./CommandCenter";
import styles from "./CommandCenterStage.module.css";

function scale() {
  return Math.min(window.innerWidth / 2560, window.innerHeight / 1440);
}

/** The reference's independent 2560 × 1440 board, fitted to the current viewport. */
export function CommandCenterStage({ navigate }: ConsoleProps) {
  const [zoom, setZoom] = useState(scale);
  useEffect(() => {
    const resize = () => {
      setZoom(scale());
    };
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
    };
  }, []);
  return (
    <div
      className={styles.wrapper}
      data-design-surface="example"
      data-source="example"
      data-command-center="true"
      data-testid="example-page-command-center-command-center"
    >
      <div
        className={`stage grid-bg ${String(styles.stage)}`}
        style={{ transform: `translate(-50%, -50%) scale(${String(zoom)})` }}
      >
        <CommandCenter />
      </div>
      <div className={styles.controls}>
        <button
          className="btn sm"
          type="button"
          onClick={() => {
            navigate(DEFAULT_ROUTE);
          }}
        >
          ← Console / 返回控制台
        </button>
        <SourceControl />
      </div>
    </div>
  );
}
