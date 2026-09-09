import { useState, type Dispatch, type SetStateAction } from "react";
import FIX_CLAIMS from "../data/claims.json";
import FIX_PROJECTS from "../data/projects.json";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { ClaimStatusBadge } from "./ClaimStatusBadge";
import { FormRow } from "./FormRow";
import visual from "./ReportForm.module.css";
import { Select } from "./Select";
import { TextInput } from "./TextInput";

/** Reference: screens/Reports.jsx; EXAMPLE ONLY. */
export const ReportForm = ({ report }: { report?: E.Report | undefined }) => {
  const { t } = useI18n();
  const [title, setTitle] = useState(report?.title ?? "");
  const [format, setFormat] = useState(report?.format ?? "preprint");
  const [project, setProject] = useState(report?.project_id ?? "proj_01K5FZ8G3X2QN4M");
  const [claims, setClaims] = useState(
    report
      ? FIX_CLAIMS.filter((c) => c.status === "VERIFIED")
          .slice(0, 3)
          .map((c) => c.id)
      : [],
  );

  return (
    <ReportFormTitle
      {...{ t, title, setTitle, project, setProject, format, setFormat, claims, setClaims }}
    />
  );
};

interface ReportFormFormCiteClaimsProps {
  t: (key: string, fallback?: string) => string;
  claims: string[];
  setClaims: Dispatch<SetStateAction<string[]>>;
}

interface ReportFormTitleProps {
  t: (key: string, fallback?: string) => string;
  title: string;
  setTitle: Dispatch<SetStateAction<string>>;
  project: string;
  setProject: Dispatch<SetStateAction<string>>;
  format: string;
  setFormat: Dispatch<SetStateAction<string>>;
  claims: string[];
  setClaims: Dispatch<SetStateAction<string[]>>;
}

function ReportFormTitle({
  t,
  title,
  setTitle,
  project,
  setProject,
  format,
  setFormat,
  claims,
  setClaims,
}: ReportFormTitleProps) {
  return (
    <div>
      <FormRow label={t("lbl.title")} required>
        <TextInput value={title} onChange={setTitle} placeholder={t("rp.form.titlePh")} />
      </FormRow>
      <FormRow label={t("lbl.project")}>
        <Select
          value={project}
          onChange={setProject}
          options={FIX_PROJECTS.map((p) => ({ value: p.id, label: p.name }))}
        />
      </FormRow>
      <FormRow label={t("rp.form.fmt")}>
        <Select
          value={format}
          onChange={setFormat}
          options={[
            { value: "abstract", label: t("rp.form.fmtAbstract") },
            { value: "preprint", label: t("rp.form.fmtPreprint") },
            { value: "workshop", label: t("rp.form.fmtWorkshop") },
            { value: "internal", label: t("rp.form.fmtInternal") },
          ]}
        />
      </FormRow>
      <ReportFormFormCiteClaims {...{ t, claims, setClaims }} />
      <ReportFormFormCompile {...{ t }} />
    </div>
  );
}

interface ReportFormFormCompileProps {
  t: (key: string, fallback?: string) => string;
}

function ReportFormFormCompile({ t }: ReportFormFormCompileProps) {
  return (
    <FormRow label={t("rp.form.compile")}>
      <div className={visual.column2}>
        <label className={visual.row3}>
          <input type="checkbox" defaultChecked className={visual.field2} />{" "}
          {t("rp.form.optFigures")}
        </label>
        <label className={visual.row4}>
          <input type="checkbox" defaultChecked className={visual.field3} />{" "}
          {t("rp.form.optManifest")}
        </label>
        <label className={visual.row5}>
          <input type="checkbox" className={visual.field4} /> {t("rp.form.optFlag")}
        </label>
      </div>
    </FormRow>
  );
}

function ReportFormFormCiteClaims({ t, claims, setClaims }: ReportFormFormCiteClaimsProps) {
  return (
    <FormRow
      label={t("rp.form.citeClaims")}
      hint={`${String(claims.length)} ${t("rp.form.citeHint")}`}
    >
      <div className={visual.column}>
        {FIX_CLAIMS.map((c) => {
          const on = claims.includes(c.id);
          return (
            <label
              key={c.id}
              className={visual.row}
              style={{ background: on ? "var(--accent-dim)" : "transparent" }}
            >
              <input
                type="checkbox"
                checked={on}
                onChange={() => {
                  setClaims(on ? claims.filter((id) => id !== c.id) : [...claims, c.id]);
                }}
                className={visual.field}
              />
              <div className={visual.surface}>
                <div className={visual.row2}>
                  <ClaimStatusBadge status={c.status} />
                  <span className={`mono ${visual.caption ?? ""}`}>{c.id.slice(4, 14)}</span>
                </div>
                <div className={visual.label}>{c.statement.slice(0, 100)}…</div>
              </div>
            </label>
          );
        })}
      </div>
    </FormRow>
  );
}
