/** Reference: screens/DryRun.jsx; EXAMPLE ONLY. */
export const fmtMinor = (m: number | null | undefined) =>
  m == null ? "UNKNOWN" : `$${(m / 100000).toFixed(2)}`;
