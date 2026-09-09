import type * as FixtureTypes from "../../fixtureTypes";
interface CompareSection8Props {
  selectedRuns: FixtureTypes.Run[];
  t: (key: string, fallback?: string) => string;
}

export function CompareSection8({ selectedRuns, t }: CompareSection8Props) {
  return (
    <div
      className="row head"
      style={{ gridTemplateColumns: `1.4fr repeat(${String(selectedRuns.length)}, 1fr) 80px` }}
    >
      <span>{t("cmp.metric")}</span>
      {selectedRuns.map((r, i) => (
        <span key={r.id}>
          {String.fromCharCode(65 + i)} · {r.label.split(" · ").pop()}
        </span>
      ))}
      <span>Δ (A→B)</span>
    </div>
  );
}
