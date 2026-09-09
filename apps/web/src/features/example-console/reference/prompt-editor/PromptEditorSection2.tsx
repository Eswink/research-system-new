import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../PromptEditor.module.css";

interface PromptEditorSection2Props {
  i: number;
  v: number;
  prompt: FixtureTypes.Prompt;
}

export function PromptEditorSection2({ i, v, prompt }: PromptEditorSection2Props) {
  return (
    <div className={visual.label5}>
      <div className={visual.surface7}>
        {i === 0
          ? "Tightened hallucination detection prompt · added confidence field"
          : i === 1
            ? "Switched from `dose` to `dose_mg` for canonical output"
            : i === 2
              ? "Added evidence_span requirement"
              : "Prompt version " + String(v)}
      </div>
      <div className={visual.caption7}>
        {new Date(new Date(prompt.updated_at).getTime() - i * 86400000 * 3)
          .toISOString()
          .slice(0, 10)}{" "}
        · {prompt.updated_by}
      </div>
    </div>
  );
}
