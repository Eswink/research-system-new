/** Reference: screens/Experiments.jsx; EXAMPLE ONLY. */
export const PriorityChip = ({ priority }: { priority: string }) => {
  const color =
    priority === "high"
      ? "var(--danger)"
      : priority === "medium"
        ? "var(--warn)"
        : "var(--fg-muted)";
  return (
    <span className="chip" style={{ color, borderColor: `${color}44` }}>
      P{priority === "high" ? "0" : priority === "medium" ? "1" : "2"} · {priority}
    </span>
  );
};
