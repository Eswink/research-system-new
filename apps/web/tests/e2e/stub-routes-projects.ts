/**
 * 项目注册表替身（EC-06 / PLAN-20260915-061）。
 *
 * 与真后端同一因果：DELETE 仅对无引用项目成功（204，并真的移出列表）；默认项目
 * 与有引用项目 409 且带 detail；未注册项目 404。静态替身无法表达"删除后列表
 * 变了"，因此这里用模块级可变状态，`resetProjectsStub()` 在每个用例前复位。
 */

import type { StubRoute } from "./stub-routes";

interface StubProject {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

const EPOCH = "1970-01-01T00:00:00+00:00";
const STAMP = "2026-09-15T00:00:00+00:00";
const DEFAULT_PROJECT_ID = "example-project";

const SEED: readonly StubProject[] = [
  {
    id: DEFAULT_PROJECT_ID,
    name: "Example ML Research",
    status: "ACTIVE",
    created_at: EPOCH,
    updated_at: EPOCH,
  },
  {
    id: "proj-funded-study",
    name: "Funded Study",
    status: "ACTIVE",
    created_at: STAMP,
    updated_at: STAMP,
  },
];

/** 引用摘要（id → 清单）：命中即 409，对齐后端 `_references()` 的语义。 */
const REFERENCES: Readonly<Record<string, string>> = { "proj-funded-study": "runs=2, drafts=1" };

let projects: StubProject[] = SEED.map((item) => ({ ...item }));
let created = 0;

/** 每个用例前复位（创建/删除跨用例会串味）。 */
export function resetProjectsStub(): void {
  projects = SEED.map((item) => ({ ...item }));
  created = 0;
}

interface StubReply {
  status: number;
  body: unknown;
}

function conflict(title: string, detail: string): StubReply {
  return { status: 409, body: { type: "about:blank", title, status: 409, detail } };
}

function notFound(id: string): StubReply {
  return {
    status: 404,
    body: {
      type: "about:blank",
      title: "Not Found",
      status: 404,
      detail: `project not found: ${id}`,
    },
  };
}

function find(id: string): StubProject | undefined {
  return projects.find((item) => item.id === id);
}

function remove(id: string): StubReply {
  const detail = REFERENCES[id];
  if (id === DEFAULT_PROJECT_ID) {
    return conflict("Project Reserved", `project ${id} is the default project`);
  }
  if (detail !== undefined) {
    return conflict("Project In Use", `project ${id} still references: ${detail}`);
  }
  projects = projects.filter((item) => item.id !== id);
  return { status: 204, body: null };
}

function deleteHandler(url: URL): StubReply {
  const id = decodeURIComponent(url.pathname.split("/").pop() ?? "");
  return find(id) === undefined ? notFound(id) : remove(id);
}

function createHandler(body: unknown): StubReply {
  created += 1;
  const name = ((body ?? {}) as { name?: string }).name ?? "stub project";
  const project: StubProject = {
    id: `proj-stub-${String(created)}`,
    name,
    status: "ACTIVE",
    created_at: STAMP,
    updated_at: STAMP,
  };
  projects = [...projects, project];
  return { status: 201, body: project };
}

function patchHandler(url: URL, body: unknown): StubReply {
  const id = decodeURIComponent(url.pathname.split("/").pop() ?? "");
  const current = find(id);
  if (current === undefined) {
    return notFound(id);
  }
  const patch = (body ?? {}) as { name?: string; status?: string };
  const updated: StubProject = {
    ...current,
    name: patch.name ?? current.name,
    status: patch.status ?? current.status,
    updated_at: STAMP,
  };
  projects = projects.map((item) => (item.id === id ? updated : item));
  return { status: 200, body: updated };
}

export const PROJECT_ROUTES: readonly StubRoute[] = [
  { method: "GET", pattern: /^\/projects$/, handler: () => ({ status: 200, body: projects }) },
  { method: "POST", pattern: /^\/projects$/, handler: (_url, body) => createHandler(body) },
  { method: "PATCH", pattern: /^\/projects\/[^/]+$/, handler: patchHandler },
  { method: "DELETE", pattern: /^\/projects\/[^/]+$/, handler: deleteHandler },
];
