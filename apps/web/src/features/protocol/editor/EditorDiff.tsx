import { Drawer } from "../../../components/Drawer";
import { useI18n } from "../../../i18n/useI18n";
import styles from "../../shared/LivePage.module.css";

/** Linear-time, lossless contiguous diff; intentionally not a minimal multi-hunk
 * merge algorithm.
 */
export function contiguousDiff(before: string, after: string) {
  const left = before.split("\n"),
    right = after.split("\n");
  let prefix = 0,
    suffix = 0;
  while (prefix < left.length && prefix < right.length && left[prefix] === right[prefix])
    prefix += 1;
  while (
    suffix < left.length - prefix &&
    suffix < right.length - prefix &&
    left[left.length - 1 - suffix] === right[right.length - 1 - suffix]
  )
    suffix += 1;
  return {
    prefix,
    removed: left.slice(prefix, left.length - suffix),
    added: right.slice(prefix, right.length - suffix),
    suffix,
  };
}

export function EditorDiff({
  before,
  after,
  open,
  onClose,
}: {
  before: string;
  after: string;
  open: boolean;
  onClose: () => void;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  const diff = contiguousDiff(before, after);
  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={zh ? "本地文本差异 · 不执行保存" : "Local text diff · does not save"}
    >
      <p className={styles.notice}>
        {zh
          ? "与最近保存或模板原文比较；连续变更区块，非自动合并。"
          : "Compared with saved/template text; contiguous change block, not an automatic merge."}
      </p>
      <p className="mono">
        {diff.prefix} unchanged · −{diff.removed.length} / +{diff.added.length} · {diff.suffix}{" "}
        unchanged
      </p>
      <h3>{zh ? "变更前" : "Before"}</h3>
      <pre className={styles.code}>{diff.removed.slice(0, 200).join("\n") || "—"}</pre>
      <h3>{zh ? "变更后" : "After"}</h3>
      <pre className={styles.code}>{diff.added.slice(0, 200).join("\n") || "—"}</pre>
      {(diff.removed.length > 200 || diff.added.length > 200) && (
        <p className={styles.notice}>
          {zh
            ? "预览各取前 200 行，原始正文未截断。"
            : "Preview limited to 200 lines per side; original text is unchanged."}
        </p>
      )}
    </Drawer>
  );
}
