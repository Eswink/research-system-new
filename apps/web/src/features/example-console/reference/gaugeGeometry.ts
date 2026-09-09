export interface GaugeGeometry {
  cx: number;
  cy: number;
  radius: number;
  start: number;
  end: number;
}

export function gaugeGeometry(size: number): GaugeGeometry {
  return {
    cx: size / 2,
    cy: size / 2 + 4,
    radius: size / 2 - 8,
    start: Math.PI * 0.85,
    end: Math.PI * 2.15,
  };
}

export function gaugeArc(geometry: GaugeGeometry, from: number, to: number): string {
  const { cx, cy, radius } = geometry;
  return [
    "M",
    cx + radius * Math.cos(from),
    cy + radius * Math.sin(from),
    "A",
    radius,
    radius,
    0,
    to - from > Math.PI ? 1 : 0,
    1,
    cx + radius * Math.cos(to),
    cy + radius * Math.sin(to),
  ].join(" ");
}

export function gaugeColor(value: number | null): string {
  if (value === null) return "var(--fg-faint)";
  if (value >= 80) return "var(--success)";
  return value >= 50 ? "var(--warn)" : "var(--danger)";
}
