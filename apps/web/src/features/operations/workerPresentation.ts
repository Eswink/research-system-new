import type { ClusterWorkerDto } from "../../api/types";

const LABELS: Readonly<Record<string, string>> = {
  REGISTERING: "注册中",
  READY: "就绪",
  BUSY: "执行中",
  DRAINING: "下线中",
  OFFLINE: "已下线",
  LOST: "失联",
};

export function workerStateLabel(state: string, zh: boolean): string {
  return zh ? (LABELS[state] ?? state) : state;
}

export function workerTone(state: string): "success" | "accent" | "danger" | "neutral" | "warn" {
  if (state === "READY") return "success";
  if (state === "BUSY") return "accent";
  if (state === "LOST") return "danger";
  if (state === "DRAINING") return "warn";
  return "neutral";
}

export function filterWorkers(workers: readonly ClusterWorkerDto[], query: string) {
  const needle = query.trim().toLocaleLowerCase();
  return workers.filter((worker) =>
    [worker.worker_ref, worker.state, worker.platform].some((value) =>
      value.toLocaleLowerCase().includes(needle),
    ),
  );
}

/** Configuration capacity is not current availability or measured GPU capacity. */
export function summarizeWorkers(workers: readonly ClusterWorkerDto[]) {
  return {
    total: workers.length,
    ready: workers.filter((worker) => worker.state === "READY").length,
    busy: workers.filter((worker) => worker.state === "BUSY").length,
    attention: workers.filter((worker) => worker.state === "LOST" || worker.state === "OFFLINE")
      .length,
    configuredConcurrency: workers.reduce((sum, worker) => sum + worker.max_concurrency, 0),
  };
}
