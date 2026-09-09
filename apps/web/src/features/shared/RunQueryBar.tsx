import { useEffect, useState } from "react";
import { useI18n } from "../../i18n/useI18n";
import styles from "./LivePage.module.css";

export function RunQueryBar({
  runId,
  onSelect,
  busy = false,
}: {
  runId: string;
  onSelect: (runId: string) => void;
  busy?: boolean;
}) {
  const { language } = useI18n();
  const [draft, setDraft] = useState(runId);
  useEffect(() => {
    setDraft(runId);
  }, [runId]);
  const zh = language === "zh";
  return (
    <form
      className={styles.query}
      onSubmit={(event) => {
        event.preventDefault();
        if (draft.trim() !== "" && !busy) onSelect(draft.trim());
      }}
    >
      <label className={styles.queryLabel}>
        <span>Run ID</span>
        <input
          className="input mono"
          value={draft}
          placeholder={zh ? "输入运行 ID" : "Enter run ID"}
          onChange={(event) => {
            setDraft(event.target.value);
          }}
        />
      </label>
      <button type="submit" className="btn" disabled={busy || draft.trim() === ""}>
        {zh ? "读取运行" : "Load run"}
      </button>
    </form>
  );
}
