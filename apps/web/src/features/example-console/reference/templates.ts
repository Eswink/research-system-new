/** Reference: screens/ProtocolEditor.jsx; EXAMPLE ONLY. */
export const TEMPLATES = {
  current: { label: "Current draft", description: "Working revision" },
  prior_study: { label: "Prior study · Med QA", description: "Reuse last month's Med QA baseline" },
  stat_heavy: {
    label: "STAT-heavy",
    description: "STANDARD + adversarial reviewers + ethics gate",
  },
  minimal: { label: "Minimal exploratory", description: "Single language · no QUALITY_GATE" },
  reset: { label: "Reset to canonical defaults", description: "1.4 canonical protocol shape" },
};
