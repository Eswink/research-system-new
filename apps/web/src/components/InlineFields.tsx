/** 控制面表格/工具条里的受控内联输入（ops 写面板与集成注册表共用）。
 *
 * 抽到 components 层是因为它在两个 feature 里是同一件事；表单自身的状态与
 * 提交语义留在各 feature，这里只管"看起来一致的输入控件"。
 */

export function InlineTextInput({
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

export function InlineSelect({
  value,
  onChange,
  options,
  placeholder,
  testid,
}: {
  value: string;
  onChange: (next: string) => void;
  options: readonly string[];
  placeholder?: string | undefined;
  testid?: string | undefined;
}) {
  return (
    <select
      className="input"
      value={value}
      data-testid={testid}
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
