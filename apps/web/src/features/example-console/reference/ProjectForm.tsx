import { useState } from "react";
import type { Project } from "../exampleTypes";
import { initialProjectDraft, projectFromDraft, type ProjectDraft } from "../projectDraft";
import { useExampleI18n } from "../useExampleI18n";
import { FormRow } from "./FormRow";
import { Select } from "./Select";
import { TagInput } from "./TagInput";
import { TextArea } from "./TextArea";
import { TextInput } from "./TextInput";

interface FieldsProps {
  draft: ProjectDraft;
  change: (patch: Partial<ProjectDraft>) => void;
}

export function ProjectForm({
  project,
  onSave,
}: {
  project?: Project | undefined;
  onSave: (project: Project) => void;
}) {
  const [draft, setDraft] = useState(() => initialProjectDraft(project));
  const [error, setError] = useState<string | null>(null);
  const { lang } = useExampleI18n();
  const change = (patch: Partial<ProjectDraft>) => {
    setDraft((current) => ({ ...current, ...patch }));
    setError(null);
  };
  return (
    <form
      id="example-project-draft"
      onSubmit={(event) => {
        event.preventDefault();
        try {
          onSave(
            projectFromDraft(draft, project, {
              id: `example-project-${crypto.randomUUID()}`,
              now: new Date().toISOString(),
            }),
          );
        } catch (cause) {
          setError(cause instanceof Error ? cause.message : "Invalid draft");
        }
      }}
    >
      <ProjectIdentityFields draft={draft} change={change} />
      <ProjectPolicyFields draft={draft} change={change} />
      <ProjectNotesFields draft={draft} change={change} />
      {error !== null && <p role="alert">{error}</p>}
      <p>
        {lang === "zh-CN"
          ? "示例编辑仅影响本页列表；导航或刷新即重置。"
          : "Example edits affect this page only; navigation or refresh resets them."}
      </p>
    </form>
  );
}

function ProjectIdentityFields({ draft, change }: FieldsProps) {
  const { t } = useExampleI18n();
  return (
    <>
      <FormRow label={t("lbl.name")} required hint={t("proj.form.nameHint")}>
        <TextInput
          value={draft.name}
          onChange={(name) => {
            change({ name });
          }}
          placeholder={t("proj.form.namePh")}
        />
      </FormRow>
      <FormRow label={t("proj.form.slug")} required hint={t("proj.form.slugHint")}>
        <TextInput
          mono
          value={draft.slug}
          placeholder="med-qa-hallucination"
          onChange={(slug) => {
            change({ slug });
          }}
        />
      </FormRow>
      <FormRow label={t("proj.form.teamTmpl")} hint={t("proj.form.teamTmplHint")}>
        <Select
          value={draft.template}
          onChange={(template) => {
            change({ template });
          }}
          options={[
            { value: "LEAN", label: "LEAN · 5-7 agents · fast iteration" },
            { value: "STANDARD", label: "STANDARD · 10-14 agents · heterogeneous review" },
            { value: "RIGOROUS", label: "RIGOROUS · 16-24 agents · adversarial + ethics" },
          ]}
        />
      </FormRow>
    </>
  );
}

function ProjectPolicyFields({ draft, change }: FieldsProps) {
  const { t } = useExampleI18n();
  return (
    <>
      <FormRow label={t("lbl.autonomy")} hint={t("proj.form.autonomyHint")}>
        <Select
          value={draft.autonomy}
          onChange={(autonomy) => {
            change({ autonomy });
          }}
          options={[
            { value: "SUPERVISED", label: "SUPERVISED · every action requires human confirm" },
            { value: "GUARDED_AUTONOMOUS", label: "GUARDED_AUTONOMOUS · pause on gates" },
            { value: "AUTONOMOUS", label: "AUTONOMOUS · pause only on hard failures" },
          ]}
        />
      </FormRow>
      <FormRow label={t("proj.form.budget")} hint={t("proj.form.budgetHint")}>
        <TextInput
          mono
          type="number"
          min="0.00001"
          step="any"
          value={draft.budget}
          onChange={(budget) => {
            change({ budget });
          }}
        />
      </FormRow>
    </>
  );
}

function ProjectNotesFields({ draft, change }: FieldsProps) {
  const { t } = useExampleI18n();
  return (
    <>
      <FormRow label={t("lbl.tags")}>
        <TagInput
          tags={draft.tags}
          onChange={(tags) => {
            change({ tags });
          }}
        />
      </FormRow>
      <FormRow label={t("lbl.notes")} hint={t("proj.form.notesHint")}>
        <TextArea
          value={draft.notes}
          rows={4}
          placeholder={t("proj.form.notesPh")}
          onChange={(notes) => {
            change({ notes });
          }}
        />
      </FormRow>
    </>
  );
}
