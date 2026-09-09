/** Reference: screens/RunsHistory.jsx; EXAMPLE ONLY. */
export const fmtVal = (v: number | null | undefined, unit: string) => {
  if (v == null) return "UNKNOWN";
  if (unit === "$") return `$${v.toFixed(2)}`;
  if (unit === "ms") return `${String(v)}ms`;
  if (unit === "rate") return `${(v * 100).toFixed(1)}%`;
  return String(v);
};
