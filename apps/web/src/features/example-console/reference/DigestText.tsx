import visual from "./DigestText.module.css";
import { Icon } from "./Icon";
import { useDigestCopy } from "./useDigestCopy";

interface Props {
  value?: string | null | undefined;
  prefix?: boolean;
  length?: number;
  label?: string;
  onCopy?: ((value: string) => void) | undefined;
}

interface DigestPresentation {
  short: string;
  truncated: boolean;
  title: string;
  copyLabel: string;
  cursor: "pointer" | "default";
}

interface DigestPresentationInput {
  value: string | null | undefined;
  prefix: boolean;
  length: number;
  label: string | undefined;
}

function digestPresentation({
  value,
  prefix,
  length,
  label,
}: DigestPresentationInput): DigestPresentation {
  const prefixEnd = prefix && value?.includes(":") === true ? value.indexOf(":") + 1 : 0;
  const end = prefixEnd > 0 ? prefixEnd + length : length;
  const short = value?.slice(0, end) ?? "UNKNOWN";
  return {
    short,
    truncated: value !== null && value !== undefined && value.length > short.length,
    title: value ?? "UNKNOWN",
    copyLabel: `Copy ${label ?? "digest"}`,
    cursor: value ? "pointer" : "default",
  };
}

/** Copy is acknowledged only after the browser confirms success. */
export function DigestText({ value, prefix = true, length = 8, label, onCopy }: Props) {
  const { copied, copy } = useDigestCopy(value, onCopy);
  const presentation = digestPresentation({ value, prefix, length, label });
  return (
    <button
      type="button"
      title={presentation.title}
      disabled={!value}
      onClick={() => {
        void copy();
      }}
      aria-label={copied ? "Copied" : presentation.copyLabel}
      className={visual.row}
      style={{ cursor: presentation.cursor }}
    >
      {label && <span className={visual.surface}>{label}</span>}
      <span>
        {presentation.short}
        {presentation.truncated ? "…" : ""}
      </span>
      <Icon name={copied ? "check" : "copy"} size={9} />
    </button>
  );
}
