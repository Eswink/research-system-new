import { type Dispatch, type SetStateAction } from "react";
import { ExampleDraftForm } from "../../ExampleDraftForm";
import { ExampleTags } from "../../ExampleTags";
import { Drawer } from "../Drawer";
import { FormRow } from "../FormRow";
import { Icon } from "../Icon";
import visual from "../SchedulesScreen.module.css";
import { TextInput } from "../TextInput";
import { SchedulesTarget } from "./SchedulesTarget";

interface SchedulesNewProps {
  drawer: { mode?: string } | null;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
  t: (key: string, fallback?: string) => string;
}

export function SchedulesNew({ drawer, setDrawer, t }: SchedulesNewProps) {
  return (
    <Drawer
      open={!!drawer}
      onClose={() => {
        setDrawer(null);
      }}
      title={t("sc.new")}
      subtitle={t("sc.newSub")}
      width={480}
      footer={
        <>
          <button
            className="btn ghost"
            onClick={() => {
              setDrawer(null);
            }}
          >
            {t("act.cancel")}
          </button>
          <button
            className={`btn primary ${visual.action ?? ""}`}
            type="submit"
            form="schedule-draft"
          >
            <Icon name="check" size={11} /> {t("act.create")}
          </button>
        </>
      }
    >
      <ExampleDraftForm id="schedule-draft">
        <FormRow label={t("lbl.name")} required>
          <TextInput name="name" placeholder={t("sc.form.namePh")} />
        </FormRow>
        <FormRow label={t("lbl.cronExpr")} required hint={t("sc.form.cronHint")}>
          <TextInput name="cron" mono placeholder={t("sc.form.cronPh")} />
        </FormRow>
        <SchedulesTarget {...{ t }} />
        <FormRow label={t("lbl.dependsOn")}>
          <ExampleTags name="dependencies" />
        </FormRow>
      </ExampleDraftForm>
    </Drawer>
  );
}
