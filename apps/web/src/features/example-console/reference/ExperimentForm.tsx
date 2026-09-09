import { useState } from "react";
import FIX_PROJECTS from "../data/projects.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./ExperimentForm.module.css";
import { FormRow } from "./FormRow";
import { Select } from "./Select";
import { TagInput } from "./TagInput";
import { TextInput } from "./TextInput";

/** Reference: screens/Experiments.jsx; EXAMPLE ONLY. */
export const ExperimentForm = () => {
  const { t } = useI18n();
  const [label, setLabel] = useState("");
  const [priority, setPriority] = useState("medium");
  const [langs, setLangs] = useState(["en", "es", "zh"]);
  const [temps, setTemps] = useState(["0.2", "0.4"]);
  const [models, setModels] = useState(["gpt-4o", "sonnet-4"]);
  const [samples, setSamples] = useState(200);

  const total = langs.length * temps.length * models.length;

  return (
    <div>
      <ExperimentIdentityFields {...{ t, label, setLabel, priority, setPriority }} />

      <div className={visual.caption}>{t("exp.form.sweep")}</div>

      <FormRow
        label={t("lbl.languages")}
        hint={`${String(langs.length)} ${t("exp.form.langHint")}`}
      >
        <TagInput tags={langs} onChange={setLangs} />
      </FormRow>
      <FormRow
        label={t("lbl.temperatures")}
        hint={`${String(temps.length)} ${t("exp.form.langHint")}`}
      >
        <TagInput tags={temps} onChange={setTemps} />
      </FormRow>
      <FormRow label={t("lbl.models")} hint={`${String(models.length)} ${t("exp.form.langHint")}`}>
        <TagInput tags={models} onChange={setModels} />
      </FormRow>
      <FormRow label={t("lbl.samples")} hint={t("exp.form.samplesHint")}>
        <TextInput
          value={samples}
          onChange={(v) => {
            setSamples(parseInt(v) || 0);
          }}
          mono
        />
      </FormRow>

      <ExperimentFormSection {...{ t, total, samples }} />
    </div>
  );
};

interface ExperimentIdentityFieldsProps {
  t: (key: string, fallback?: string) => string;
  label: string;
  setLabel: (value: string) => void;
  priority: string;
  setPriority: (value: string) => void;
}

function ExperimentIdentityFields(props: ExperimentIdentityFieldsProps) {
  return (
    <>
      <FormRow label={props.t("lbl.label")} required hint={props.t("exp.form.labelHint")}>
        <TextInput
          value={props.label}
          onChange={props.setLabel}
          mono
          placeholder="my-experiment-name"
        />
      </FormRow>
      <FormRow label={props.t("lbl.project")}>
        <Select
          name="project"
          defaultValue="proj_01K5FZ8G3X2QN4M"
          options={FIX_PROJECTS.map((project) => ({ value: project.id, label: project.name }))}
        />
      </FormRow>
      <FormRow label={props.t("lbl.priority")}>
        <Select
          value={props.priority}
          onChange={props.setPriority}
          options={[
            { value: "high", label: props.t("exp.form.priorityHigh") },
            { value: "medium", label: props.t("exp.form.priorityMid") },
            { value: "low", label: props.t("exp.form.priorityLow") },
          ]}
        />
      </FormRow>
    </>
  );
}

interface ExperimentFormSectionProps {
  t: (key: string, fallback?: string) => string;
  total: number;
  samples: number;
}

function ExperimentFormSection({ t, total, samples }: ExperimentFormSectionProps) {
  return (
    <div className={visual.surface}>
      <div className={visual.caption2}>{t("exp.projection")}</div>
      <div className={visual.row}>
        <div>
          <div className={visual.label}>{total}</div>
          <div className={visual.caption3}>{t("exp.cells")}</div>
        </div>
        <div>
          <div className={visual.label2}>{(total * samples).toLocaleString()}</div>
          <div className={visual.caption4}>{t("exp.samples")}</div>
        </div>
        <div>
          <div className={visual.label3}>~${(total * samples * 0.008).toFixed(0)}</div>
          <div className={visual.caption5}>{t("exp.estCost")}</div>
        </div>
        <div>
          <div className={visual.label4}>~{Math.round((total * samples * 0.4) / 60)}m</div>
          <div className={visual.caption6}>{t("exp.estDuration")}</div>
        </div>
      </div>
    </div>
  );
}
