import { useState } from "react";

import { api } from "../../api/client";
import type { ResourceKind } from "../../api/types";
import { ErrorState } from "../../components/States";
import styles from "../shared/LivePage.module.css";

/** 库条目创建条（name 必填；描述可选）。成功回调触发列表刷新。 */
export function ResourceCreateBar({
  kind,
  zh,
  onCreated,
}: {
  kind: ResourceKind;
  zh: boolean;
  onCreated: () => void;
}) {
  const state = useCreateState(kind, onCreated);
  return (
    <form
      className={styles.toolbar}
      onSubmit={(event) => {
        event.preventDefault();
        state.submit();
      }}
    >
      <input
        className="input"
        value={state.name}
        placeholder={zh ? "名称" : "Name"}
        onChange={(event) => {
          state.setName(event.target.value);
        }}
      />
      <input
        className="input"
        value={state.description}
        placeholder={zh ? "描述（可选）" : "Description (optional)"}
        onChange={(event) => {
          state.setDescription(event.target.value);
        }}
      />
      <button className="btn" type="submit" disabled={state.busy || state.name.trim() === ""}>
        {zh ? "添加" : "Add"}
      </button>
      {state.error !== null && <ErrorState message={state.error} />}
    </form>
  );
}

function useCreateState(kind: ResourceKind, onCreated: () => void) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = (): void => {
    if (name.trim() === "" || busy) return;
    setBusy(true);
    setError(null);
    void api
      .createLibrary({ kind, name: name.trim(), description: description.trim() })
      .then(() => {
        setName("");
        setDescription("");
        setBusy(false);
        onCreated();
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : String(reason));
        setBusy(false);
      });
  };
  return { name, setName, description, setDescription, busy, error, submit };
}
