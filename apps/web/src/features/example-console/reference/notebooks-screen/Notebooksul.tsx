import visual from "../NotebooksScreen.module.css";

export function Notebooksul() {
  return (
    <ul className={visual.label6}>
      <li>
        Generic-name substitution: "amoxicilina" → "amoxicillin" was accepted but "0.5g" → "500mg"
        was frequently converted incorrectly.
      </li>
      <li>
        Dosage-unit confusion: mg vs g vs mL — most failures are unit-conversion in Spanish and
        Chinese.
      </li>
      <li>
        Frequency prepositions: "cada 8 horas" and "q8h" are not being unified in the eval pipeline.
      </li>
    </ul>
  );
}
