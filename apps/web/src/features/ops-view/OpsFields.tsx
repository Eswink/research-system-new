/** ops 写面的受控输入（三个表单共用；保持各表单函数在 50 行内）。 */

export function OpsTextInput({
  value,
  onChange,
  placeholder,
  testid,
}: {
  value: string;
  onChange: (next: string) => void;
  placeholder: string;
  testid?: string | undefined;
}) {
  return (
    <input
      className="input"
      value={value}
      placeholder={placeholder}
      data-testid={testid}
      onChange={(event) => {
        onChange(event.target.value);
      }}
    />
  );
}

export function OpsSelect({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: string;
  onChange: (next: string) => void;
  options: readonly string[];
  placeholder?: string | undefined;
}) {
  return (
    <select
      className="input"
      value={value}
      onChange={(event) => {
        onChange(event.target.value);
      }}
    >
      {placeholder !== undefined && <option value="">{placeholder}</option>}
      {options.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </select>
  );
}
