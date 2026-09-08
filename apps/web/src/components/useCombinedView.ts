/** 多请求聚合：全部成功才 ready；部分失败显示首个错误。 */

import type { DataView } from "./DataViewFrame";

export function useCombinedView(): {
  combine: <T>(views: DataView<T>[]) => DataView<T[]>;
  ready: boolean;
} {
  return {
    combine: <T,>(views: DataView<T>[]): DataView<T[]> => {
      const loading = views.some((view) => view.loading);
      const error = views.find((view) => view.error !== null)?.error ?? null;
      const data =
        views.every((view) => view.data !== null)
          ? views.map((view) => view.data as T)
          : null;
      return { data, loading, error };
    },
    ready: true,
  };
}
