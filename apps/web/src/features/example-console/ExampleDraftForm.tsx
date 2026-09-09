import { useState, type ReactNode } from "react";
import styles from "./ExampleDraftForm.module.css";
import { useExampleI18n } from "./useExampleI18n";

/** A design draft, not a registered resource. No API, storage or execution side effects. */
export function ExampleDraftForm({ id, children }: { id: string; children: ReactNode }) {
  const { lang } = useExampleI18n();
  const [saved, setSaved] = useState<readonly [string, string][] | null>(null);
  return (
    <form
      id={id}
      onChange={() => {
        setSaved(null);
      }}
      onSubmit={(event) => {
        event.preventDefault();
        const entries = [...new FormData(event.currentTarget)].flatMap(([key, value]) =>
          typeof value === "string" ? [[key, value] as [string, string]] : [],
        );
        setSaved(entries);
      }}
    >
      {children}
      {saved !== null && (
        <div className={styles.receipt} data-testid="example-draft-receipt">
          <p role="status">
            {lang === "zh-CN"
              ? "示例草稿仅保存在当前抽屉内存。未注册、提交或发布后端资源；关闭后清除。"
              : [
                  "Example draft retained in this drawer only. No backend resource was ",
                  "registered, submitted or published. Closing clears it.",
                ].join("")}
          </p>
          <dl>
            {saved.map(([key, value], index) => (
              <div key={`${key}-${String(index)}`}>
                <dt>{key}</dt>
                <dd>{value || "—"}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </form>
  );
}
