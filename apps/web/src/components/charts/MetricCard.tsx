import type { ReactNode } from "react";

import { Icon } from "../Icon";
import { num } from "./fmt";
import styles from "./MetricCard.module.css";
import { Sparkline } from "./Sparkline";

/** 指标卡：标签 + 大数值 + 可选 sparkline/进度条/趋势；unknown 有独立通道。 */
export function MetricCard({
  label,
  value,
  sub,
  bar,
  barColor,
  trend,
  unknownWarn = false,
  spark,
  sparkColor,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode | undefined;
  bar?: number | undefined;
  barColor?: string | undefined;
  trend?: number | undefined;
  unknownWarn?: boolean;
  spark?: readonly number[] | undefined;
  sparkColor?: string | undefined;
}) {
  return (
    <div className={`panel ${styles.card ?? ""}`}>
      <MetricHead label={label} unknownWarn={unknownWarn} trend={trend} />
      <div className={styles.valueRow}>
        <div className={styles.value}>{value}</div>
        {spark !== undefined && (
          <Sparkline data={spark} width={80} height={22} stroke={sparkColor ?? "var(--accent)"} />
        )}
      </div>
      {sub !== undefined && <div className={styles.sub}>{sub}</div>}
      {bar !== undefined && (
        <div className={styles.track}>
          <div
            className={styles.fill}
            style={{
              width: `${num(Math.min(bar, 1) * 100)}%`,
              background: barColor ?? "var(--accent)",
            }}
          />
        </div>
      )}
    </div>
  );
}

function MetricHead({
  label,
  unknownWarn,
  trend,
}: {
  label: string;
  unknownWarn: boolean;
  trend?: number | undefined;
}) {
  return (
    <div className={styles.head} data-unknown={unknownWarn || undefined}>
      {unknownWarn && <Icon name="q" size={10} />}
      {label}
      {trend !== undefined && (
        <span className={trend >= 0 ? styles.up : styles.down}>
          {trend >= 0 ? "▲" : "▼"} {Math.abs(trend).toFixed(1)}%
        </span>
      )}
    </div>
  );
}
