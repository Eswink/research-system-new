import visual from "../DatasetsScreen.module.css";

export function Datasetstable() {
  return (
    <table className={visual.caption6}>
      <thead>
        <tr className={visual.surface9}>
          {["id", "language", "question", "gold_answer", "model_output"].map((c) => (
            <th key={c} className={visual.surface10}>
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {(
          [
            [
              "mqa_001",
              "es",
              "¿Cuál es la dosis de amoxicilina…",
              "500mg tid×7d",
              "500 mg cada 8h",
            ],
            ["mqa_002", "zh", "阿莫西林的成人剂量是…", "500mg tid×7d", "0.5g q8h"],
            ["mqa_003", "en", "Adult dose of amoxicillin…", "500mg tid×7d", "500mg q8h"],
            ["mqa_004", "ar", "ما هي جرعة الأموكسيسيلين…", "500mg tid×7d", "500 mg every 8 hours"],
          ] as const
        ).map((row, i) => (
          <tr key={i} className={visual.surface11}>
            {row.map((c, j) => (
              <td
                key={j}
                className={visual.surface12}
                style={{ color: j === 0 ? "var(--accent)" : "var(--fg-muted)" }}
              >
                {c}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
