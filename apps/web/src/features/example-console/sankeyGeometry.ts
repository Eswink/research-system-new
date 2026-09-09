import type { SankeyFlow, SankeyNode } from "./exampleTypes";
import type { GraphSize } from "./graphGeometry";

export interface SankeyPosition {
  x: number;
  y: number;
  h: number;
  scale: number;
}
const COLUMNS: Readonly<Record<string, number>> = {
  project: 0,
  model: 1,
  task: 2,
  source: 0,
  target: 2,
  mid: 1,
};

function flowTotals(flows: SankeyFlow[]) {
  const incoming = new Map<string, number>(),
    outgoing = new Map<string, number>();
  for (const flow of flows) {
    if (!Number.isFinite(flow.value) || flow.value < 0) continue;
    outgoing.set(flow.from, (outgoing.get(flow.from) ?? 0) + flow.value);
    incoming.set(flow.to, (incoming.get(flow.to) ?? 0) + flow.value);
  }
  return (id: string) => Math.max(incoming.get(id) ?? 0, outgoing.get(id) ?? 0);
}

export function layoutSankey(nodes: SankeyNode[], flows: SankeyFlow[], size: GraphSize) {
  const columns = new Map<number, SankeyNode[]>();
  for (const node of nodes) {
    const column = node.col ?? COLUMNS[node.type] ?? 0;
    const entries = columns.get(column) ?? [];
    entries.push(node);
    columns.set(column, entries);
  }
  const keys = [...columns.keys()].sort((a, b) => a - b);
  const total = flowTotals(flows);
  const positions = new Map<string, SankeyPosition>();
  keys.forEach((key, index) => {
    const entries = columns.get(key) ?? [];
    const sum = entries.reduce((acc, node) => acc + total(node.id), 0);
    const scale = (size.height - 40) / (sum || 1);
    let y = 20;
    for (const node of entries) {
      const h = total(node.id) * scale;
      const x = 60 + index * ((size.width - 120) / Math.max(1, keys.length - 1));
      positions.set(node.id, { x, y, h, scale });
      y += h + 6;
    }
  });
  return positions;
}

export function sankeyPaths(flows: SankeyFlow[], positions: Map<string, SankeyPosition>) {
  const outgoing = new Map<string, number>(),
    incoming = new Map<string, number>();
  return flows.flatMap((flow, index) => {
    const s = positions.get(flow.from),
      t = positions.get(flow.to);
    if (!s || !t || !Number.isFinite(flow.value) || flow.value < 0) return [];
    const sh = flow.value * s.scale,
      th = flow.value * t.scale;
    const sy = s.y + (outgoing.get(flow.from) ?? 0) + sh / 2;
    const ty = t.y + (incoming.get(flow.to) ?? 0) + th / 2;
    outgoing.set(flow.from, (outgoing.get(flow.from) ?? 0) + sh);
    incoming.set(flow.to, (incoming.get(flow.to) ?? 0) + th);
    const mx = (s.x + t.x) / 2;
    return [
      {
        index,
        d: ["M", s.x + 8, sy, "C", mx, sy, mx, ty, t.x - 8, ty].join(" "),
        width: Math.max(sh, th),
      },
    ];
  });
}
