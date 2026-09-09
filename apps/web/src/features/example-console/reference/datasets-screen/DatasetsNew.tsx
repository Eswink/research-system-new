import { type Dispatch, type SetStateAction } from "react";
import { ExampleDraftForm } from "../../ExampleDraftForm";
import { ExampleTags } from "../../ExampleTags";
import visual from "../DatasetsScreen.module.css";
import { Drawer } from "../Drawer";
import { FormRow } from "../FormRow";
import { Icon } from "../Icon";
import { Select } from "../Select";
import { TextInput } from "../TextInput";

interface DatasetsNewProps {
  drawer: { mode?: string } | null;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
  t: (key: string, fallback?: string) => string;
}

export function DatasetsNew({ drawer, setDrawer, t }: DatasetsNewProps) {
  return (
    <Drawer
      open={!!drawer}
      onClose={() => {
        setDrawer(null);
      }}
      title={t("ds.new")}
      subtitle={t("ds.newSub")}
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
            form="dataset-draft"
          >
            <Icon name="check" size={11} /> {t("act.register")}
          </button>
        </>
      }
    >
      <DatasetsNewName {...{ t }} />
    </Drawer>
  );
}

interface DatasetsNewNameProps {
  t: (key: string, fallback?: string) => string;
}

function DatasetsNewName({ t }: DatasetsNewNameProps) {
  return (
    <ExampleDraftForm id="dataset-draft">
      <FormRow label={t("lbl.name")} required>
        <TextInput name="name" placeholder="my-dataset-name" mono />
      </FormRow>
      <FormRow label={t("lbl.version")} required>
        <TextInput name="version" placeholder="v1.0.0" mono />
      </FormRow>
      <FormRow label={t("ds.form.source")} required>
        <Select
          name="source"
          defaultValue="upload"
          options={[
            { value: "upload", label: t("ds.form.srcUpload") },
            { value: "s3", label: t("ds.form.srcS3") },
            { value: "derive", label: t("ds.form.srcDerive") },
          ]}
        />
      </FormRow>
      <FormRow label={t("ds.form.upload")}>
        <div className={visual.surface24}>
          <Icon name="external" size={20} className={visual.surface25} />
          <div className={visual.label10}>{t("ds.form.dropHint")}</div>
          <div className={visual.caption12}>{t("ds.form.dropSpec")}</div>
        </div>
      </FormRow>
      <FormRow label={t("lbl.tags")}>
        <ExampleTags name="tags" initial={["draft"]} />
      </FormRow>
    </ExampleDraftForm>
  );
}
