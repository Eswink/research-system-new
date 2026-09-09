import { type Dispatch, type SetStateAction } from "react";
import FIX_CLAIMS from "../../data/claims.json";
import { ClaimStatusBadge } from "../ClaimStatusBadge";
import { Drawer } from "../Drawer";
import { FormRow } from "../FormRow";
import { Icon } from "../Icon";
import visual from "../NotebooksScreen.module.css";
import { TextArea } from "../TextArea";
import { TextInput } from "../TextInput";

interface NotebooksNewProps {
  drawer: { mode?: string } | null;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
  t: (key: string, fallback?: string) => string;
}

export function NotebooksNew({ drawer, setDrawer, t }: NotebooksNewProps) {
  return (
    <Drawer
      open={!!drawer}
      onClose={() => {
        setDrawer(null);
      }}
      title={t("nb.new")}
      subtitle={t("nb.newSub")}
      width={480}
      footer={<NotebookDrawerFooter {...{ setDrawer, t }} />}
    >
      <FormRow label={t("lbl.title")} required>
        <TextInput placeholder={t("nb.form.titlePh")} />
      </FormRow>
      <FormRow label={t("lbl.body")} hint={t("proj.form.notesHint")}>
        <TextArea rows={8} placeholder={t("nb.form.bodyPh")} />
      </FormRow>
      <FormRow label={t("nb.form.link")}>
        <div className={visual.column3}>
          {FIX_CLAIMS.slice(0, 4).map((c) => (
            <label key={c.id} className={visual.row5}>
              <input type="checkbox" className={visual.field} />
              <ClaimStatusBadge status={c.status} />
              <span className={visual.surface9}>{c.statement.slice(0, 60)}…</span>
            </label>
          ))}
        </div>
      </FormRow>
    </Drawer>
  );
}

function NotebookDrawerFooter({ setDrawer, t }: Pick<NotebooksNewProps, "setDrawer" | "t">) {
  const close = () => {
    setDrawer(null);
  };
  return (
    <>
      <button className="btn ghost" onClick={close}>
        {t("act.cancel")}
      </button>
      <button className={`btn primary ${visual.action ?? ""}`} onClick={close}>
        <Icon name="check" size={11} /> {t("act.save")}
      </button>
    </>
  );
}
