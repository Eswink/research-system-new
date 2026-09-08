/** 编辑器字段原语（PhaseCard 等区块共用；Field 包装 + 样式绑定）。 */

import { Field } from "../../../../components/Field";
import { cx } from "../../../../components/cx";
import styles from "./Sections.module.css";

export function TextField(props: {
  fieldIndex: number;
  name: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
}): React.JSX.Element {
  const inputId = "phase-" + String(props.fieldIndex) + "-" + props.name;
  return (
    <Field label={props.label} htmlFor={inputId}>
      <input
        id={inputId}
        className={cx(styles.input, styles.monoInput)}
        value={props.value}
        onChange={(event) => {
          props.onChange(event.target.value);
        }}
      />
    </Field>
  );
}

export function SelectField(props: {
  fieldIndex: number;
  name: string;
  label: string;
  value: string;
  options: readonly { value: string; label: string }[];
  className?: string | undefined;
  onChange: (value: string) => void;
}): React.JSX.Element {
  const inputId = "phase-" + String(props.fieldIndex) + "-" + props.name;
  const selectClass =
    props.className === undefined
      ? cx(styles.input, styles.monoInput)
      : cx(styles.input, styles.monoInput, props.className);
  return (
    <Field label={props.label} htmlFor={inputId}>
      <select
        id={inputId}
        className={selectClass}
        value={props.value}
        onChange={(event) => {
          props.onChange(event.target.value);
        }}
      >
        {props.options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </Field>
  );
}

export function CommaList(props: {
  index: number;
  label: string;
  value: string[];
  placeholder: string;
  tooltip: string;
  onChange: (items: string[]) => void;
}): React.JSX.Element {
  return (
    <Field label={props.label} tooltip={props.tooltip}>
      <input
        className={cx(styles.input, styles.monoInput)}
        value={props.value.join(", ")}
        placeholder={props.placeholder}
        onChange={(event) => {
          props.onChange(splitComma(event.target.value));
        }}
      />
    </Field>
  );
}

function splitComma(raw: string): string[] {
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}
