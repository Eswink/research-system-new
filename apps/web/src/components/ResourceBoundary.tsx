import type { ReactNode } from "react";
import type { ResourceState } from "../hooks/useResource";
import { useI18n } from "../i18n/useI18n";
import { ErrorState, ForbiddenState, LoadingState, UnavailableState } from "./States";

type QueryState = Pick<
  ResourceState<unknown>,
  "phase" | "error" | "forbidden" | "unavailable" | "stale"
>;

/** Query failure is not an empty result, and cannot change a page's data source. */
export function ResourceBoundary({ state, children }: { state: QueryState; children: ReactNode }) {
  const { language, t } = useI18n();
  if (state.phase === "error") {
    const message = state.error ?? t("state.error");
    if (state.forbidden) return <ForbiddenState message={message} />;
    if (state.unavailable)
      return (
        <UnavailableState
          title={language === "zh" ? "真实接口暂不可用" : "Live endpoint unavailable"}
          reason={message}
        />
      );
    return <ErrorState message={message} />;
  }
  return (
    <>
      {state.phase === "loading" && <LoadingState message={t("state.loading")} />}
      {state.phase !== "loading" || state.stale ? children : null}
    </>
  );
}
