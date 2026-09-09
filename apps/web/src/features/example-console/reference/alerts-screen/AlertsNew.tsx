import { type Dispatch, type SetStateAction } from "react";
import { ExampleDraftForm } from "../../ExampleDraftForm";
import { ExampleTags } from "../../ExampleTags";
import visual from "../AlertsScreen.module.css";
import { Drawer } from "../Drawer";
import { FormRow } from "../FormRow";
import { Icon } from "../Icon";
import { Select } from "../Select";
import { TextArea } from "../TextArea";
import { TextInput } from "../TextInput";
import { AlertsScope } from "./AlertsScope";

interface AlertsNewProps {
  drawer: { mode?: string } | null;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
  t: (key: string, fallback?: string) => string;
}

export function AlertsNew({ drawer, setDrawer, t }: AlertsNewProps) {
  return <AlertsNewNew {...{ drawer, setDrawer, t }} />;
}

interface AlertsNewNewProps {
  drawer: { mode?: string } | null;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
  t: (key: string, fallback?: string) => string;
}

function AlertsNewNew({ drawer, setDrawer, t }: AlertsNewNewProps) {
  return (
    <Drawer
      open={!!drawer}
      onClose={() => {
        setDrawer(null);
      }}
      title={t("al.new")}
      subtitle={t("al.newSub")}
      width={520}
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
          <button className={`btn primary ${visual.action ?? ""}`} type="submit" form="alert-draft">
            <Icon name="check" size={11} /> {t("al.createRule")}
          </button>
        </>
      }
    >
      <AlertsNewName {...{ t }} />
    </Drawer>
  );
}

interface AlertsNewNameProps {
  t: (key: string, fallback?: string) => string;
}

function AlertsNewName({ t }: AlertsNewNameProps) {
  return (
    <ExampleDraftForm id="alert-draft">
      <FormRow label={t("lbl.name")} required>
        <TextInput name="name" placeholder={t("al.form.namePh")} />
      </FormRow>
      <AlertsScope {...{ t }} />
      <FormRow label={t("lbl.condition")} hint={t("al.form.condHint")}>
        <TextArea name="condition" mono rows={2} placeholder={t("al.form.condPh")} />
      </FormRow>
      <FormRow label={t("lbl.severity")}>
        <Select
          name="severity"
          defaultValue="medium"
          options={[
            { value: "high", label: t("al.form.sevHigh") },
            { value: "medium", label: t("al.form.sevMid") },
            { value: "low", label: t("al.form.sevLow") },
          ]}
        />
      </FormRow>
      <FormRow label={t("lbl.channels")}>
        <ExampleTags name="channels" initial={["slack:#research-ops"]} />
      </FormRow>
      <FormRow label={t("lbl.suppression")} hint={t("al.form.suppressHint")}>
        <TextInput name="suppression" mono placeholder="30" />
      </FormRow>
    </ExampleDraftForm>
  );
}
