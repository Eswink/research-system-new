/* Chart primitives — SVG, small, monochromatic-aware.
   All charts follow the four-channel encoding rule:
   status is never conveyed via color alone. */

// ─────────────────────────────────────────────────────────
// Sparkline — inline tiny line chart
// data: [n0, n1, ...]  width/height in px
// ─────────────────────────────────────────────────────────
const Sparkline = ({ data, width = 96, height = 22, stroke = "var(--accent)", fill = "var(--accent-dim)", strokeWidth = 1.4 }) => {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1);
  const points = data.map((v, i) => [i * step, height - ((v - min) / range) * (height - 4) - 2]);
  const linePath = "M " + points.map(p => p.join(" ")).join(" L ");
  const areaPath = linePath + ` L ${width} ${height} L 0 ${height} Z`;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: "inline-block", verticalAlign: "middle" }}>
      <path d={areaPath} fill={fill} stroke="none"/>
      <path d={linePath} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx={points[points.length-1][0]} cy={points[points.length-1][1]} r={2} fill={stroke}/>
    </svg>
  );
};

// ─────────────────────────────────────────────────────────
// BarSeries — stacked bar chart, tiny.
// data: [{ label, values: [n1,n2,n3] }]   series: [{ key, color }]
// ─────────────────────────────────────────────────────────
const BarSeries = ({ data, series, width = 480, height = 160, showLabels = true, showGrid = true }) => {
  if (!data || !data.length) return null;
  const pad = { l: 32, r: 8, t: 8, b: showLabels ? 22 : 8 };
  const w = width - pad.l - pad.r;
  const h = height - pad.t - pad.b;
  const totals = data.map(d => d.values.reduce((a,b) => a+b, 0));
  const max = Math.max(...totals) || 1;
  const barW = w / data.length * 0.7;
  const gap = w / data.length * 0.3;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {showGrid && [0, 0.25, 0.5, 0.75, 1].map((r, i) => (
        <g key={i}>
          <line x1={pad.l} x2={pad.l + w} y1={pad.t + h - r * h} y2={pad.t + h - r * h} stroke="var(--border-subtle)" strokeWidth="1"/>
          <text x={pad.l - 6} y={pad.t + h - r * h + 3} textAnchor="end" fontSize="9" fontFamily="var(--font-mono)" fill="var(--fg-faint)">{Math.round(max * r)}</text>
        </g>
      ))}
      {data.map((d, i) => {
        let stackY = 0;
        return (
          <g key={i} transform={`translate(${pad.l + i * (barW + gap) + gap/2},0)`}>
            {series.map((s, j) => {
              const v = d.values[j] || 0;
              const bh = (v / max) * h;
              const y = pad.t + h - stackY - bh;
              stackY += bh;
              return <rect key={j} x={0} y={y} width={barW} height={bh} fill={s.color} rx="1"/>;
            })}
            {showLabels && (
              <text x={barW / 2} y={height - 6} textAnchor="middle" fontSize="9" fontFamily="var(--font-mono)" fill="var(--fg-faint)">{d.label}</text>
            )}
          </g>
        );
      })}
    </svg>
  );
};

// ─────────────────────────────────────────────────────────
// Donut — % gauge / share.
// values: [{ label, value, color }]
// ─────────────────────────────────────────────────────────
const Donut = ({ values, size = 88, thickness = 12, center }) => {
  const cx = size / 2, cy = size / 2;
  const r = (size - thickness) / 2;
  const total = values.reduce((a, v) => a + v.value, 0) || 1;
  let acc = 0;
  const C = 2 * Math.PI * r;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--bg-sunken)" strokeWidth={thickness}/>
      {values.map((v, i) => {
        const frac = v.value / total;
        const dash = frac * C;
        const gap = C - dash;
        const rot = (acc / total) * 360 - 90;
        acc += v.value;
        return (
          <circle key={i} cx={cx} cy={cy} r={r} fill="none"
            stroke={v.color} strokeWidth={thickness}
            strokeDasharray={`${dash} ${gap}`}
            transform={`rotate(${rot} ${cx} ${cy})`}
            strokeLinecap="butt"/>
        );
      })}
      {center && (
        <foreignObject x="0" y="0" width={size} height={size}>
          <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", pointerEvents: "none" }}>
            {center}
          </div>
        </foreignObject>
      )}
    </svg>
  );
};

// ─────────────────────────────────────────────────────────
// Gauge — health score with tick marks
// value 0..100
// ─────────────────────────────────────────────────────────
const HealthGauge = ({ value = 82, size = 120, label = "HEALTH" }) => {
  const cx = size / 2, cy = size / 2 + 4;
  const r = size / 2 - 8;
  const startA = Math.PI * 0.85;
  const endA = Math.PI * 0.15 + 2 * Math.PI;
  const span = endA - startA;
  const valA = startA + (value / 100) * span;
  const arc = (a1, a2) => {
    const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
    const x2 = cx + r * Math.cos(a2), y2 = cy + r * Math.sin(a2);
    const large = (a2 - a1) > Math.PI ? 1 : 0;
    return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
  };
  const color = value == null ? "var(--fg-faint)"
    : value >= 80 ? "var(--success)"
    : value >= 50 ? "var(--warn)"
    : "var(--danger)";

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <path d={arc(startA, endA)} fill="none" stroke="var(--bg-sunken)" strokeWidth="8" strokeLinecap="round"/>
      {value != null && <path d={arc(startA, valA)} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"/>}
      {/* tick marks */}
      {[0,25,50,75,100].map(t => {
        const a = startA + (t/100) * span;
        const x1 = cx + (r - 12) * Math.cos(a), y1 = cy + (r - 12) * Math.sin(a);
        const x2 = cx + (r - 6) * Math.cos(a), y2 = cy + (r - 6) * Math.sin(a);
        return <line key={t} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--fg-faint)" strokeWidth="1"/>;
      })}
      <text x={cx} y={cy - 4} textAnchor="middle" fontSize="24" fontFamily="var(--font-mono)" fontWeight="500" fill={color}>
        {value == null ? "—" : value}
      </text>
      <text x={cx} y={cy + 14} textAnchor="middle" fontSize="9" fontFamily="var(--font-mono)" fill="var(--fg-faint)" letterSpacing="0.1em">
        {label}
      </text>
    </svg>
  );
};

// ─────────────────────────────────────────────────────────
// Heatmap — day × slot grid (like GitHub contributions).
// data: 2D array of intensity 0..1; xLabels, yLabels optional
// ─────────────────────────────────────────────────────────
const Heatmap = ({ data, xLabels = [], yLabels = [], cell = 14, gap = 2, color = "var(--accent)" }) => {
  const rows = data.length;
  const cols = data[0]?.length || 0;
  const w = cols * (cell + gap) + 40;
  const h = rows * (cell + gap) + 20;
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      {yLabels.map((l, i) => (
        <text key={i} x={4} y={12 + i * (cell + gap) + cell/1.4} fontSize="9" fontFamily="var(--font-mono)" fill="var(--fg-faint)">{l}</text>
      ))}
      {data.map((row, y) => row.map((v, x) => (
        <rect key={`${x}-${y}`} x={38 + x * (cell + gap)} y={4 + y * (cell + gap)} width={cell} height={cell} rx="2"
          fill={color} fillOpacity={0.1 + v * 0.9}/>
      )))}
      {xLabels.map((l, i) => (
        <text key={i} x={38 + i * (cell + gap) + cell/2} y={h - 4} textAnchor="middle" fontSize="8" fontFamily="var(--font-mono)" fill="var(--fg-faint)">{l}</text>
      ))}
    </svg>
  );
};

// ─────────────────────────────────────────────────────────
// Sankey — flows between nodes across 2-3 columns.
// nodes: [{ id, label, type, col? }]
// flows: [{ from, to, value }]
// ─────────────────────────────────────────────────────────
const Sankey = ({ nodes, flows, width = 640, height = 320 }) => {
  // Bucket nodes into columns by type or explicit col
  const typeOrder = { project: 0, model: 1, task: 2, source: 0, target: 2, mid: 1 };
  const cols = {};
  nodes.forEach(n => {
    const c = n.col != null ? n.col : (typeOrder[n.type] ?? 0);
    if (!cols[c]) cols[c] = [];
    cols[c].push(n);
  });
  const colIds = Object.keys(cols).sort();
  const colX = i => 60 + i * ((width - 120) / (colIds.length - 1));

  // Sum inflow/outflow per node
  const inflow = {}, outflow = {};
  flows.forEach(f => {
    outflow[f.from] = (outflow[f.from] || 0) + f.value;
    inflow[f.to] = (inflow[f.to] || 0) + f.value;
  });

  // Total per column for height scaling
  const colTotal = {};
  colIds.forEach(c => {
    colTotal[c] = cols[c].reduce((a, n) => a + Math.max(outflow[n.id] || 0, inflow[n.id] || 0), 0);
  });
  const scale = c => (height - 40) / (colTotal[c] || 1);

  // Position nodes vertically
  const pos = {}; // id → { x, y, h }
  colIds.forEach(c => {
    let y = 20;
    cols[c].forEach(n => {
      const h = Math.max(outflow[n.id] || 0, inflow[n.id] || 0) * scale(c);
      pos[n.id] = { x: colX(colIds.indexOf(c)), y, h };
      y += h + 6;
    });
  });

  const modelColor = "var(--accent)";
  const projectColor = "var(--fg-muted)";
  const taskColor = "var(--success)";
  const nodeColor = n => n.type === "project" ? projectColor : n.type === "task" ? taskColor : modelColor;

  // Track offset within source and target for each flow
  const srcOff = {}, tgtOff = {};

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* flows */}
      {flows.map((f, i) => {
        const s = pos[f.from], t = pos[f.to];
        if (!s || !t) return null;
        const sh = f.value * scale(colIds.find(c => cols[c].includes(nodes.find(n => n.id === f.from))));
        const th = f.value * scale(colIds.find(c => cols[c].includes(nodes.find(n => n.id === f.to))));
        const sy = s.y + (srcOff[f.from] || 0) + sh / 2;
        const ty = t.y + (tgtOff[f.to] || 0) + th / 2;
        srcOff[f.from] = (srcOff[f.from] || 0) + sh;
        tgtOff[f.to] = (tgtOff[f.to] || 0) + th;
        const mx = (s.x + t.x) / 2;
        const path = `M ${s.x + 8} ${sy} C ${mx} ${sy}, ${mx} ${ty}, ${t.x - 8} ${ty}`;
        return <path key={i} d={path} fill="none" stroke={modelColor} strokeOpacity="0.18" strokeWidth={Math.max(sh, th)} strokeLinecap="butt"/>;
      })}
      {/* nodes */}
      {nodes.map(n => {
        const p = pos[n.id];
        if (!p) return null;
        return (
          <g key={n.id}>
            <rect x={p.x} y={p.y} width="8" height={p.h} rx="2" fill={nodeColor(n)}/>
            <text x={p.x + 14} y={p.y + p.h / 2 + 3} fontSize="10" fontFamily="var(--font-mono)" fill="var(--fg)" opacity="0.9">{n.label}</text>
          </g>
        );
      })}
    </svg>
  );
};

// ─────────────────────────────────────────────────────────
// LineSeries — multi-line, with legend
// data: [{ label, values: [n0..nN] }]   xLabels: string[]
// ─────────────────────────────────────────────────────────
const LineSeries = ({ data, xLabels, width = 640, height = 220, colors, yFormat = (v) => v, showGrid = true }) => {
  const pad = { l: 40, r: 12, t: 10, b: 24 };
  const w = width - pad.l - pad.r;
  const h = height - pad.t - pad.b;
  const all = data.flatMap(d => d.values);
  const max = Math.max(...all) || 1;
  const min = Math.min(0, ...all);
  const range = max - min || 1;
  const step = w / ((data[0]?.values.length || 1) - 1);
  const palette = colors || ["var(--accent)", "var(--success)", "var(--warn)", "var(--unknown)", "var(--danger)", "var(--fg-muted)"];

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {showGrid && [0, 0.25, 0.5, 0.75, 1].map((r, i) => (
        <g key={i}>
          <line x1={pad.l} x2={pad.l + w} y1={pad.t + h - r*h} y2={pad.t + h - r*h} stroke="var(--border-subtle)"/>
          <text x={pad.l - 6} y={pad.t + h - r*h + 3} textAnchor="end" fontSize="9" fontFamily="var(--font-mono)" fill="var(--fg-faint)">{yFormat(Math.round(min + range*r))}</text>
        </g>
      ))}
      {data.map((d, di) => {
        const pts = d.values.map((v, i) => [pad.l + i*step, pad.t + h - ((v - min)/range)*h]);
        const dPath = "M " + pts.map(p => p.join(" ")).join(" L ");
        return (
          <g key={di}>
            <path d={dPath} fill="none" stroke={palette[di % palette.length]} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            {pts.map((p, i) => <circle key={i} cx={p[0]} cy={p[1]} r="1.6" fill={palette[di % palette.length]}/>)}
          </g>
        );
      })}
      {xLabels && xLabels.map((l, i) => (
        <text key={i} x={pad.l + i*step} y={height - 6} textAnchor="middle" fontSize="9" fontFamily="var(--font-mono)" fill="var(--fg-faint)">{l}</text>
      ))}
    </svg>
  );
};

// ─────────────────────────────────────────────────────────
// ForceGraph — small force-directed layout (pre-computed
// so we don't have to run physics live). Nodes get random
// positions with deterministic seed.
// nodes: [{ id, label, group }]  edges: [{ from, to }]
// ─────────────────────────────────────────────────────────
const ForceGraph = ({ nodes, edges, width = 480, height = 320, groupColors, onNodeClick, selectedId }) => {
  const seed = (str) => {
    let h = 2166136261;
    for (let i = 0; i < str.length; i++) h = Math.imul(h ^ str.charCodeAt(i), 16777619);
    return () => { h = Math.imul(h ^ (h >>> 15), 2246822507); h = Math.imul(h ^ (h >>> 13), 3266489909); return ((h ^ (h >>> 16)) >>> 0) / 4294967295; };
  };
  const positions = {};
  nodes.forEach(n => {
    const rng = seed(n.id);
    positions[n.id] = { x: 40 + rng() * (width - 80), y: 40 + rng() * (height - 80) };
  });
  // Simple 60-iter spring simulation
  for (let iter = 0; iter < 80; iter++) {
    const forces = {};
    nodes.forEach(n => forces[n.id] = { x: 0, y: 0 });
    // Repulsion
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = positions[nodes[i].id], b = positions[nodes[j].id];
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist2 = Math.max(dx*dx + dy*dy, 100);
        const k = 800 / dist2;
        forces[nodes[i].id].x += dx * k;
        forces[nodes[i].id].y += dy * k;
        forces[nodes[j].id].x -= dx * k;
        forces[nodes[j].id].y -= dy * k;
      }
    }
    // Attraction along edges
    edges.forEach(e => {
      const a = positions[e.from], b = positions[e.to];
      if (!a || !b) return;
      const dx = b.x - a.x, dy = b.y - a.y;
      forces[e.from].x += dx * 0.02;
      forces[e.from].y += dy * 0.02;
      forces[e.to].x -= dx * 0.02;
      forces[e.to].y -= dy * 0.02;
    });
    nodes.forEach(n => {
      positions[n.id].x += forces[n.id].x * 0.05;
      positions[n.id].y += forces[n.id].y * 0.05;
      positions[n.id].x = Math.max(30, Math.min(width - 30, positions[n.id].x));
      positions[n.id].y = Math.max(30, Math.min(height - 30, positions[n.id].y));
    });
  }

  const gc = groupColors || {};
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {edges.map((e, i) => {
        const a = positions[e.from], b = positions[e.to];
        if (!a || !b) return null;
        const highlighted = selectedId && (e.from === selectedId || e.to === selectedId);
        return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
          stroke={highlighted ? "var(--accent)" : "var(--border)"}
          strokeWidth={highlighted ? "1.5" : "1"}/>;
      })}
      {nodes.map(n => {
        const p = positions[n.id];
        const color = gc[n.group] || "var(--accent)";
        const isSel = n.id === selectedId;
        const dim = selectedId && !isSel && n.highlighted === false;
        return (
          <g key={n.id} transform={`translate(${p.x} ${p.y})`}
            style={{ cursor: onNodeClick ? "pointer" : "default", opacity: dim ? 0.35 : 1 }}
            onClick={() => onNodeClick?.(n.id)}>
            <circle r={isSel ? 6 : 4} fill={color} stroke={isSel ? "var(--fg)" : "var(--bg-panel)"} strokeWidth={isSel ? "2" : "1.5"}/>
            <text x="8" y="3" fontSize="9" fontFamily="var(--font-mono)"
              fill={isSel ? "var(--fg)" : "var(--fg-muted)"}
              fontWeight={isSel ? 600 : 400}>{n.label}</text>
          </g>
        );
      })}
    </svg>
  );
};

// ─────────────────────────────────────────────────────────
// MetricCard — reusable across dashboards
// ─────────────────────────────────────────────────────────
const MetricCard = ({ label, value, sub, bar, barColor, trend, unknownWarn, spark, sparkColor }) => (
  <div className="panel" style={{ padding: 14, display: "flex", flexDirection: "column", gap: 6 }}>
    <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: unknownWarn ? "var(--unknown)" : "var(--fg-faint)", letterSpacing: "0.08em", textTransform: "uppercase", display: "flex", alignItems: "center", gap: 6 }}>
      {unknownWarn && <Icon name="q" size={10}/>}
      {label}
      {trend != null && (
        <span style={{ marginLeft: "auto", color: trend >= 0 ? "var(--success)" : "var(--danger)", fontFamily: "var(--font-mono)", fontSize: 10 }}>
          {trend >= 0 ? "▲" : "▼"} {Math.abs(trend).toFixed(1)}%
        </span>
      )}
    </div>
    <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 12 }}>
      <div style={{ fontSize: 22, fontFamily: "var(--font-mono)", fontWeight: 500, letterSpacing: "-0.02em" }}>{value}</div>
      {spark && <Sparkline data={spark} width={80} height={22} stroke={sparkColor || "var(--accent)"}/>}
    </div>
    {sub && <div style={{ fontSize: 11, color: "var(--fg-muted)", lineHeight: 1.45 }}>{sub}</div>}
    {bar != null && (
      <div style={{ height: 3, background: "var(--bg-sunken)", borderRadius: 2, overflow: "hidden", marginTop: 2 }}>
        <div style={{ width: `${Math.min(bar, 1) * 100}%`, height: "100%", background: barColor || "var(--accent)" }}/>
      </div>
    )}
  </div>
);

Object.assign(window, { Sparkline, BarSeries, Donut, HealthGauge, Heatmap, Sankey, LineSeries, ForceGraph, MetricCard });
