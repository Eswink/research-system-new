import { Field } from "../../../../components/Field";
import { cx } from "../../../../components/cx";
import { SectionHeader } from "../EditorLayout";
import type { ProtocolForm } from "../protocolDocument";
import styles from "./Sections.module.css";

/** 标识区块：protocol.id（schema 约束）+ version（SemVer）+ 阶段计数投影 */
export function IdentitySection({
  form,
  revision,
}: {
  form: ProtocolForm;
  revision: number | null;
}) {
  const phaseNoun = form.phases.length === 1 ? "phase" : "phases";
  const phaseSummary = String(form.phases.length) + " " + phaseNoun;
  return (
    <div>
      <SectionHeader
        title="Identity"
        subtitle="Protocol identity and version (read-only; from the draft YAML)"
        extra={
          <span className={cx("chip", styles.accentChip)}>{phaseSummary}</span>
        }
      />
      <IdField value={form.id} />
      <VersionField value={form.version} />
      <Field
        label="saved revision"
        tooltip="Latest saved draft revision; revision 1 = initial save"
      >
        <span className="chip mono">{revision === null ? "not saved" : String(revision)}</span>
      </Field>
    </div>
  );
}

function IdField({ value }: { value: string }): React.JSX.Element {
  return (
    <Field
      label="id"
      tooltip="Schema pattern: ^[a-z0-9]+(?:_[a-z0-9]+)*_v[0-9]+_[0-9]+_[0-9]+$"
      locked
      htmlFor="protocol-id"
    >
      <input
        id="protocol-id"
        className={cx(styles.input, styles.monoInput)}
        value={value}
        readOnly
      />
    </Field>
  );
}

function VersionField({ value }: { value: string }): React.JSX.Element {
  return (
    <Field
      label="version"
      tooltip="Protocol version (SemVer); matches the engineering VERSION line"
      locked
    >
      <input className={cx(styles.input, styles.monoInput)} value={value} readOnly />
    </Field>
  );
}
