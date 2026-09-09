import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import { Icon } from "../Icon";
import visual from "../PromptEditor.module.css";
import { PromptStatusBadge } from "../PromptStatusBadge";
import { PromptEditorSection3 } from "./PromptEditorSection3";

interface PromptEditorSectionProps {
  prompt: FixtureTypes.Prompt;
  t: (key: string, fallback?: string) => string;
  setTab: Dispatch<SetStateAction<string>>;
  tab: string;
}

export function PromptEditorSection({ prompt, t, setTab, tab }: PromptEditorSectionProps) {
  const updatedDate = new Date(prompt.updated_at).toISOString().slice(0, 10);
  return (
    <div className={visual.surface}>
      <div className={visual.row}>
        <div className={visual.surface2}>
          <div className={visual.caption}>{prompt.tags.join(" · ")}</div>
          <div className={visual.label}>{prompt.name}</div>
        </div>
        <div className={visual.row2}>
          <button className="btn sm">
            <Icon name="fork" size={10} /> {t("act.fork")}
          </button>
          <button className="btn sm">
            <Icon name="external" size={10} /> {t("act.test")}
          </button>
          <button className="btn primary sm">
            <Icon name="check" size={10} /> {t("act.publish")}
          </button>
        </div>
      </div>

      <div className={visual.row3}>
        <PromptStatusBadge status={prompt.status} />
        <span className="mono">{prompt.latest_version}</span>
        <span>·</span>
        <span>
          {prompt.versions} {t("pr.versions")}
        </span>
        <span>·</span>
        <span>
          {t("pr.updated")} {updatedDate} {t("pr.by")} {prompt.updated_by}
        </span>
      </div>

      <PromptEditorSection3 {...{ t, setTab, tab }} />
    </div>
  );
}
