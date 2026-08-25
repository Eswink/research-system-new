import type { ChangeEvent } from "react";

export function TextField({
  label,
  value,
  onChange,
  placeholder,
  autoComplete,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  autoComplete?: string;
  required?: boolean;
}) {
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.value);
  };
  return (
    <label>
      {label}
      <input
        required={required}
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        autoComplete={autoComplete}
      />
    </label>
  );
}

export function PasswordField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.value);
  };
  return (
    <label>
      {label}
      <input type="password" value={value} onChange={handleChange} autoComplete="off" />
    </label>
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
  const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    onChange(event.target.value);
  };
  return (
    <label>
      {label}
      <select value={value} onChange={handleChange}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}