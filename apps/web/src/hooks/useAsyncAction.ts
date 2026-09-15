import { useCallback, useState } from "react";

/**
 * 写操作（mutating request）的 busy/error 状态机。
 *
 * 控制面所有写面板共用：一次只跑一个任务（busy 期间忽略重复触发），
 * 成功后回调 onDone（通常用于 reload 读面），失败保留可读错误文案。
 * 写面的事实一律以随后的读面重新加载为准，不在本地猜测结果。
 */
export function useAsyncAction(onDone: () => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const run = useCallback(
    (task: () => Promise<unknown>) => {
      if (busy) return;
      setBusy(true);
      setError(null);
      task()
        .then(() => {
          setBusy(false);
          onDone();
        })
        .catch((reason: unknown) => {
          setError(reason instanceof Error ? reason.message : String(reason));
          setBusy(false);
        });
    },
    [busy, onDone],
  );
  return { busy, error, run };
}
