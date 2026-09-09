/** Reference: screens/RunsHistory.jsx; EXAMPLE ONLY. */
export const fmtDuration = (s: number | null) => {
  if (s == null) return "UNKNOWN";
  if (s < 60) return `${String(s)}s`;
  if (s < 3600) return `${String(Math.round(s / 60))}m`;
  return `${String(Math.floor(s / 3600))}h ${String(Math.round((s % 3600) / 60))}m`;
};
