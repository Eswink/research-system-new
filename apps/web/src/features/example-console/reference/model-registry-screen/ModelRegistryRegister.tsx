import { type Dispatch, type SetStateAction } from "react";
import { ExampleDraftForm } from "../../ExampleDraftForm";
import { ExampleTags } from "../../ExampleTags";
import { Drawer } from "../Drawer";
import { FormRow } from "../FormRow";
import { Icon } from "../Icon";
import visual from "../ModelRegistryScreen.module.css";
import { TextInput } from "../TextInput";
import { ModelRegistryFormProvider } from "./ModelRegistryFormProvider";

interface ModelRegistryRegisterProps {
  drawer: { mode?: string } | null;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
  t: (key: string, fallback?: string) => string;
}

export function ModelRegistryRegister({ drawer, setDrawer, t }: ModelRegistryRegisterProps) {
  return (
    <Drawer
      open={!!drawer}
      onClose={() => {
        setDrawer(null);
      }}
      title={t("mr.register")}
      subtitle={t("mr.drawer.subtitle")}
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
          <button className={`btn primary ${visual.action ?? ""}`} type="submit" form="model-draft">
            <Icon name="check" size={11} /> {t("act.register")}
          </button>
        </>
      }
    >
      <ModelRegistryRegisterFormFamily {...{ t }} />
    </Drawer>
  );
}

interface ModelRegistryRegisterFormFamilyProps {
  t: (key: string, fallback?: string) => string;
}

function ModelRegistryRegisterFormFamily({ t }: ModelRegistryRegisterFormFamilyProps) {
  return (
    <ExampleDraftForm id="model-draft">
      <FormRow label={t("mr.form.family")} required>
        <TextInput name="family" mono placeholder="e.g. claude-opus" />
      </FormRow>
      <ModelRegistryFormProvider {...{ t }} />
      <FormRow label={t("mr.form.modelId")} required hint={t("mr.form.modelIdHint")}>
        <TextInput name="modelId" mono placeholder="claude-opus-4-1-20250805" />
      </FormRow>
      <FormRow label={t("mr.form.released")}>
        <TextInput name="released" mono placeholder="2025-08-05" />
      </FormRow>
      <FormRow label={t("mr.form.context")}>
        <TextInput name="context" mono placeholder="200000" />
      </FormRow>
      <FormRow label={t("mr.form.license")}>
        <TextInput name="license" placeholder="proprietary · MIT · apache-2.0" />
      </FormRow>
      <FormRow label={t("mr.form.tags")}>
        <ExampleTags name="tags" />
      </FormRow>
    </ExampleDraftForm>
  );
}
