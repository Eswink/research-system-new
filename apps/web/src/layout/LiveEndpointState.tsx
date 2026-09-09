import type { ReactNode } from "react";
import { ErrorState, LoadingState } from "../components/States";
import type { EndpointsState } from "../hooks/useEndpoints";
import { useI18n } from "../i18n/useI18n";

/** A failed live request remains an error, never a silent example fallback. */
export function LiveEndpointState({
  state,
  children,
}: {
  state: EndpointsState;
  children: ReactNode;
}) {
  const { language } = useI18n();
  const zh = language === "zh";
  if (state.loading) {
    return (
      <div data-testid="app-loading">
        <LoadingState message={zh ? "正在读取端点…" : "Loading endpoints…"} />
      </div>
    );
  }
  if (state.error !== null) {
    return (
      <section data-testid="app-error">
        <ErrorState message={state.error} />
        <p>
          {zh
            ? "真实端点读取失败，未替换为示例。其他页面仍可访问；可重试或显式查看示例。"
            : "Endpoint loading failed. Other pages remain accessible; retry or select Example."}
        </p>
        <button type="button" className="btn" onClick={state.refresh}>
          {zh ? "重新读取" : "Retry"}
        </button>
      </section>
    );
  }
  return children;
}
