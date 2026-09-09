/** Reference: screens/Timeline.jsx; EXAMPLE ONLY. */
export const getEventTypeStyle = (type: string) => {
  if (type.startsWith("task.failed")) return { icon: "x", color: "var(--danger)" };
  if (type.startsWith("task.attempt")) return { icon: "clock", color: "var(--warn)" };
  if (type.startsWith("task")) return { icon: "hex", color: "var(--fg-muted)" };
  if (type.startsWith("agent")) return { icon: "circle", color: "var(--accent)" };
  if (type.startsWith("tool")) return { icon: "square", color: "var(--fg-muted)" };
  if (type.startsWith("policy")) return { icon: "shield", color: "var(--accent)" };
  if (type.startsWith("evidence")) return { icon: "diamond", color: "var(--success)" };
  if (type.startsWith("budget")) return { icon: "diamond", color: "var(--warn)" };
  if (type.startsWith("claim")) return { icon: "check", color: "var(--success)" };
  if (type.startsWith("gate")) return { icon: "shield", color: "var(--unknown)" };
  if (type.startsWith("experiment")) return { icon: "flask", color: "var(--accent)" };
  return { icon: "circle-o", color: "var(--fg-muted)" };
};
