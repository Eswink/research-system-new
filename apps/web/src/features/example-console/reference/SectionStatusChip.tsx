import visual from "./SectionStatusChip.module.css";

/** Reference: screens/Reports.jsx; EXAMPLE ONLY. */
export const SectionStatusChip = ({ status }: { status: string }) => {
  const map: Record<string, { color: string; label: string }> = {
    complete: { color: "var(--success)", label: "complete" },
    "in-progress": { color: "var(--accent)", label: "in-progress" },
    draft: { color: "var(--warn)", label: "draft" },
    todo: { color: "var(--fg-faint)", label: "todo" },
  };
  const c = map[status] ?? { color: "var(--unknown)", label: status };
  return (
    <span
      className={`chip ${visual.caption ?? ""}`}
      style={{ color: c.color, borderColor: `${c.color}44` }}
    >
      {c.label}
    </span>
  );
};
