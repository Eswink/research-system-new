import { useId, type ChangeEvent } from "react";

import { Field } from "../../../components/Field";
import { Icon } from "../../../components/Icon";
import styles from "./steps.module.css";

export function TextField({
  label,
  value,
  onChange,
  placeholder,
  autoComplete,
  required = false,
  mono = false,
  hint,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  autoComplete?: string;
  required?: boolean;
  mono?: boolean;
  hint?: string;
}) {
  const id = useId();
  return (
    <Field label={label} htmlFor={id} hint={hint}>
      <input
        id={id}
        className={mono ? "input mono" : "input"}
        required={required}
        value={value}
        onChange={(event: ChangeEvent<HTMLInputElement>) => {
          onChange(event.target.value);
        }}
        placeholder={placeholder}
        autoComplete={autoComplete}
      />
    </Field>
  );
}

export function PasswordField({
  label,
  value,
  onChange,
  hint,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  hint?: string;
}) {
  const id = useId();
  return (
    <Field label={label} htmlFor={id} hint={hint}>
      <div className={styles.inputWrap}>
        <input
          id={id}
          className="input"
          type="password"
          value={value}
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            onChange(event.target.value);
          }}
          autoComplete="off"
        />
        <Icon name="lock" size={12} className={styles.inputLock} />
      </div>
    </Field>
  );
}

export function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly { value: string; label: string }[];
}) {
  const id = useId();
  return (
    <Field label={label} htmlFor={id}>
      <select
        id={id}
        className="input mono"
        value={value}
        onChange={(event: ChangeEvent<HTMLSelectElement>) => {
          onChange(event.target.value);
        }}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </Field>
  );
}
