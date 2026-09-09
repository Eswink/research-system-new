import { FormRow } from "../FormRow";
import { Select } from "../Select";

interface SchedulesTargetProps {
  t: (key: string, fallback?: string) => string;
}

export function SchedulesTarget({ t }: SchedulesTargetProps) {
  return (
    <FormRow label={t("lbl.target")}>
      <Select
        name="target"
        defaultValue="experiment"
        options={[
          { value: "experiment", label: t("sc.form.tgtExp") },
          { value: "probe", label: t("sc.form.tgtProbe") },
          { value: "report", label: t("sc.form.tgtRep") },
          { value: "graph", label: t("sc.form.tgtGraph") },
        ]}
      />
    </FormRow>
  );
}
