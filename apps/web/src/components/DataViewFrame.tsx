/**
 * 视图状态覆盖（PLAN-20260908-033 阶段五）。
 *
 * 每个页面必须覆盖：loading / error / empty / ready 四态；
 * 403 由 ErrorState 单独标识（P5 默认拒绝要可见）。
 */

import type { ReactElement, ReactNode } from "react";

export interface DataView<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/** 统一判断 403（Problem detail 由后端映射） */
export function isForbidden(error: string | null): boolean {
  return error !== null && (error.includes("403") || error.toLowerCase().includes("forbidden"));
}

export function DataViewFrame<T>({
  view,
  emptyMessage,
  loadingMessage,
  render,
}: {
  view: DataView<T>;
  emptyMessage: string;
  loadingMessage: string;
  render: (data: T) => ReactNode;
}): ReactElement {
  if (view.loading) {
    return (
      <div className="chip" role="status" data-testid="view-loading">
        {loadingMessage}
      </div>
    );
  }
  if (view.error !== null) {
    return (
      <div role="alert" data-testid="view-error">
        <span className="chip">{view.error}</span>
      </div>
    );
  }
  if (view.data === null) {
    return (
      <span className="empty-mark" data-testid="view-empty">
        {emptyMessage}
      </span>
    );
  }
  return <>{render(view.data)}</>;
}
