import type { GraphEdge, GraphNode } from "./exampleTypes";

export interface Point {
  x: number;
  y: number;
}
interface Particle extends Point {
  id: string;
  fx: number;
  fy: number;
}
export interface GraphSize {
  width: number;
  height: number;
}

function seededRandom(key: string): () => number {
  let hash = 2166136261;
  for (let i = 0; i < key.length; i++) hash = Math.imul(hash ^ key.charCodeAt(i), 16777619);
  return () => {
    hash = Math.imul(hash ^ (hash >>> 15), 2246822507);
    hash = Math.imul(hash ^ (hash >>> 13), 3266489909);
    return ((hash ^ (hash >>> 16)) >>> 0) / 4294967295;
  };
}

function repel(a: Particle, b: Particle): void {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  const force = 800 / Math.max(dx * dx + dy * dy, 100);
  a.fx += dx * force;
  a.fy += dy * force;
  b.fx -= dx * force;
  b.fy -= dy * force;
}

function accumulateForces(particles: Particle[], edges: GraphEdge[]): void {
  for (const p of particles) {
    p.fx = 0;
    p.fy = 0;
  }
  particles.forEach((a, i) => {
    for (const b of particles.slice(i + 1)) repel(a, b);
  });
  const byId = new Map(particles.map((p) => [p.id, p]));
  for (const edge of edges) {
    const a = byId.get(edge.from);
    const b = byId.get(edge.to);
    if (!a || !b) continue;
    const dx = (b.x - a.x) * 0.02;
    const dy = (b.y - a.y) * 0.02;
    a.fx += dx;
    a.fy += dy;
    b.fx -= dx;
    b.fy -= dy;
  }
}

/** Same seeded spring layout as the supplied design; no runtime telemetry or random input. */
export function layoutGraph(nodes: GraphNode[], edges: GraphEdge[], size: GraphSize) {
  const particles = nodes.map((node) => {
    const random = seededRandom(node.id);
    return {
      id: node.id,
      x: 40 + random() * (size.width - 80),
      y: 40 + random() * (size.height - 80),
      fx: 0,
      fy: 0,
    };
  });
  for (let iteration = 0; iteration < 80; iteration++) {
    accumulateForces(particles, edges);
    for (const p of particles) {
      p.x = Math.max(30, Math.min(size.width - 30, p.x + p.fx * 0.05));
      p.y = Math.max(30, Math.min(size.height - 30, p.y + p.fy * 0.05));
    }
  }
  return new Map<string, Point>(particles.map((p) => [p.id, { x: p.x, y: p.y }]));
}
