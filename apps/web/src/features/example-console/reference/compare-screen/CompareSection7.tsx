import { TrendBadge } from "../TrendBadge";

interface CompareSection7Props {
  delta: number | null;
  meta: { key: string; a: number; b: number; delta: number; better: boolean; unit: string };
}

export function CompareSection7({ delta, meta }: CompareSection7Props) {
  return (
    <div>
      {delta != null && (
        <TrendBadge
          delta={delta * (meta.unit === "rate" ? 100 : 1)}
          inverted={meta.better === delta < 0}
          format={(v) =>
            meta.unit === "$"
              ? `${v > 0 ? "+" : "-"}$${v.toFixed(2)}`
              : meta.unit === "ms"
                ? `${v > 0 ? "+" : ""}${String(Math.round(v))}`
                : meta.unit === "rate"
                  ? `${v > 0 ? "+" : ""}${v.toFixed(1)}pp`
                  : v.toFixed(1)
          }
        />
      )}
    </div>
  );
}
