import { useState } from "react";
import { useExampleField } from "../fieldContext";
import { Icon } from "./Icon";
import visual from "./TagInput.module.css";

export function TagInput({
  tags = [],
  onChange,
  name,
}: {
  tags?: string[];
  onChange: (tags: string[]) => void;
  name?: string;
}) {
  const [input, setInput] = useState("");
  const field = useExampleField();
  const add = () => {
    const value = input.trim();
    if (value !== "" && !tags.includes(value)) onChange([...tags, value]);
    setInput("");
  };
  return (
    <div className={visual.row}>
      {name !== undefined && <input type="hidden" name={name} value={tags.join(", ")} />}
      {tags.map((tag, index) => (
        <TagChip key={`${tag}-${String(index)}`} {...{ tag, index, tags, onChange }} />
      ))}
      <input
        {...field}
        required={false}
        value={input}
        className={visual.field}
        onChange={(event) => {
          setInput(event.target.value);
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            add();
          }
        }}
        placeholder={tags.length > 0 ? "" : "Add tag…"}
      />
    </div>
  );
}

interface TagChipProps {
  tag: string;
  index: number;
  tags: string[];
  onChange: (tags: string[]) => void;
}

function TagChip({ tag, index, tags, onChange }: TagChipProps) {
  return (
    <span className={`chip ${visual.surface ?? ""}`}>
      {tag}
      <button
        type="button"
        aria-label={`Remove ${tag}`}
        className={visual.action}
        onClick={() => {
          onChange(tags.filter((_, itemIndex) => itemIndex !== index));
        }}
      >
        <Icon name="x" size={8} />
      </button>
    </span>
  );
}
