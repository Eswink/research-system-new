import { useEffect, useRef, useState } from "react";

interface CommandState<Result> {
  pending: boolean;
  result: Result | null;
  error: string | null;
}

/** Explicit mutations only: no effect-driven dispatch, optimistic truth, retries
 * or cancellation claims.
 */
export function useCommand<Argument, Result>(
  execute: (argument: Argument) => Promise<Result>,
  onSuccess?: (result: Result) => void,
) {
  const [state, setState] = useState<CommandState<Result>>({
    pending: false,
    result: null,
    error: null,
  });
  const active = useRef(false);
  const mounted = useRef(true);
  const isMounted = () => mounted.current;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const run = async (argument: Argument) => {
    if (active.current || !isMounted()) return;
    active.current = true;
    setState({ pending: true, error: null, result: null });
    try {
      const result = await execute(argument);
      if (isMounted()) {
        setState({ pending: false, result, error: null });
        onSuccess?.(result);
      }
    } catch (cause) {
      if (isMounted())
        setState({
          pending: false,
          result: null,
          error: cause instanceof Error ? cause.message : "Command failed",
        });
    } finally {
      active.current = false;
    }
  };
  return { ...state, run };
}
