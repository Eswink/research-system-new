/**
 * ToolPack 写面替身（PLAN-20260915-065 EC-02 / AC-05）。
 *
 * 与真后端同一因果：install 时**重算内容 digest** 并要求与声明值相等（不符 → 422）；
 * 权限扩张（新增 capability / network domain / credential）只登记为**待批准**，
 * 生效版本与生效 digest 不变；approve-update 才替换；REVOKE 终态。
 * 静态替身无法表达这些状态迁移，因此用模块级可变状态 + `resetToolPackStub()`。
 *
 * digest 口径镜像 `packages/domain/serialization.py`（canonical JSON：键排序、
 * 无多余空白、UTF-8）。这里是**替身**不是权威实现——权威口径由后端测试与
 * live 套件（真实 uvicorn）证明。
 */

import { createHash } from "node:crypto";

import type { StubRoute } from "./stub-routes";

/** 替身 manifest 输入（内容字段；digest 由内容算出，不手填）。 */
export interface StubManifestInput {
  id: string;
  version?: string;
  capabilities?: string[];
  networkDomains?: string[];
  credentials?: string[];
}

interface StubPack {
  id: string;
  state: string;
  manifest: Record<string, unknown>;
  pending: Record<string, unknown> | null;
  revoked_reason: string | null;
}

const NOW = "2026-09-16T00:00:00Z";

let packs: StubPack[] = [];

/** 每个用例前复位（pack 状态跨用例会串味）。 */
export function resetToolPackStub(): void {
  packs = [];
}

/** canonical JSON（键递归排序、无空白）——与域口径同规则的最小子集。 */
function canonical(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map(canonical).join(",")}]`;
  }
  if (value !== null && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>).sort(([a], [b]) =>
      a < b ? -1 : 1,
    );
    const body = entries.map(([key, item]) => `${JSON.stringify(key)}:${canonical(item)}`);
    return `{${body.join(",")}}`;
  }
  return JSON.stringify(value);
}

export function stubContentDigest(content: Record<string, unknown>): string {
  const hex = createHash("sha256").update(canonical(content), "utf8").digest("hex");
  return `sha256:${hex}`;
}

/** 构造带自洽 digest 的 manifest 文档（测试用它填表单）。 */
export function stubManifestDocument(input: StubManifestInput): Record<string, unknown> {
  const content = {
    id: input.id,
    version: input.version ?? "1.0.0",
    source: "fixture://console-stub",
    resolved_revision: `rev-${input.version ?? "1.0.0"}`,
    license: "MIT",
    tools: [],
    skills: [],
    requested_capabilities: [...(input.capabilities ?? [])].sort(),
    network_domains: [...(input.networkDomains ?? [])].sort(),
    credentials: [...(input.credentials ?? [])].sort().map((name) => ({
      name,
      scope: "TOOL",
      required: true,
    })),
  };
  return { ...content, digest: stubContentDigest(content), signature: null };
}

/** 内容字段（digest 不参与，与域 `_manifest_content_dict` 同口径）。 */
function contentOf(document: Record<string, unknown>): Record<string, unknown> {
  const content: Record<string, unknown> = { ...document };
  delete content.digest;
  delete content.signature;
  return content;
}

function strList(document: Record<string, unknown>, key: string): string[] {
  const value = document[key];
  return Array.isArray(value) ? value.map((item) => String(item)) : [];
}

function credentialNames(document: Record<string, unknown>): string[] {
  const value = document.credentials;
  if (!Array.isArray(value)) return [];
  return value.map((item) => String((item as Record<string, unknown>).name ?? ""));
}

/** 扩张差集：新增 capability / network domain / credential（空 = 无扩张）。 */
function permissionDiff(current: Record<string, unknown>, next: Record<string, unknown>) {
  const added = (pick: (doc: Record<string, unknown>) => string[]): string[] => {
    const before = new Set(pick(current));
    return pick(next)
      .filter((item) => !before.has(item))
      .sort();
  };
  const capabilities = (doc: Record<string, unknown>) => strList(doc, "requested_capabilities");
  const domains = (doc: Record<string, unknown>) => strList(doc, "network_domains");
  return {
    added_capabilities: added(capabilities),
    added_network_domains: added(domains),
    added_credentials: added(credentialNames),
  };
}

function hasExpansion(diff: ReturnType<typeof permissionDiff>): boolean {
  return (
    diff.added_capabilities.length > 0 ||
    diff.added_network_domains.length > 0 ||
    diff.added_credentials.length > 0
  );
}

function packDto(pack: StubPack): Record<string, unknown> {
  const manifest = pack.manifest;
  const pending = pack.pending;
  return {
    id: pack.id,
    state: pack.state,
    digest: String(manifest.digest),
    version: String(manifest.version),
    source: String(manifest.source),
    resolved_revision: String(manifest.resolved_revision),
    license: String(manifest.license),
    capabilities: strList(manifest, "requested_capabilities"),
    network_domains: strList(manifest, "network_domains"),
    credential_names: credentialNames(manifest),
    tool_ids: [],
    installed_at: NOW,
    revoked_reason: pack.revoked_reason,
    pending:
      pending === null
        ? null
        : {
            digest: String(pending.digest),
            version: String(pending.version),
            capabilities: strList(pending, "requested_capabilities"),
            diff: permissionDiff(manifest, pending),
            note: "",
          },
    catalog_digest_active: pack.state === "INSTALLED",
  };
}

/** 与后端 `PACK_NOTE` 同文案：面板脚注的呈现与真链路一致。 */
const NOTE =
  "install 由控制面重算 manifest 内容 digest 并要求与声明的 digest 相等（pin 与提交内容自洽）；" +
  "权限扩张（新增 capability / network domain / credential）不立即生效——登记为待批准更新，" +
  "approve-update 后才替换；REVOKE 为终态。生效版本与待批准版本分别呈现。";

type StubResult = { status: number; body: unknown };

/** 提交结果体（与真后端 DTO 同形：status + pack + diff + note）。 */
function submitResult(
  status: number,
  name: string,
  outcome: { pack: StubPack; diff: unknown },
): StubResult {
  const body = { status: name, pack: packDto(outcome.pack), diff: outcome.diff, note: NOTE };
  return { status, body };
}

function replacePack(next: StubPack): StubPack {
  packs = packs.map((item) => (item.id === next.id ? next : item));
  return next;
}

function submit(document: Record<string, unknown>): StubResult {
  if (stubContentDigest(contentOf(document)) !== String(document.digest ?? "")) {
    return {
      status: 422,
      body: {
        title: "Invalid ToolPack Manifest",
        detail: `tool pack ${String(document.id)} digest mismatch: content does not match declared`,
      },
    };
  }
  const id = String(document.id);
  const existing = packs.find((item) => item.id === id);
  if (existing === undefined) {
    const created: StubPack = {
      id,
      state: "INSTALLED",
      manifest: document,
      pending: null,
      revoked_reason: null,
    };
    packs = [...packs, created];
    return submitResult(201, "installed", { pack: created, diff: null });
  }
  if (existing.state === "REVOKED") {
    return {
      status: 409,
      body: { title: "ToolPack Conflict", detail: `revoked tool pack is terminal: ${id}` },
    };
  }
  if (existing.manifest.digest === document.digest) {
    return submitResult(201, "unchanged", { pack: existing, diff: null });
  }
  const diff = permissionDiff(existing.manifest, document);
  if (hasExpansion(diff)) {
    const pending = replacePack({ ...existing, pending: document });
    return submitResult(201, "pending_approval", { pack: pending, diff });
  }
  const applied = replacePack({ ...existing, manifest: document, pending: null });
  return submitResult(201, "updated", { pack: applied, diff: null });
}

function findPack(url: URL): StubPack | undefined {
  const id = url.pathname.split("/").at(-2) ?? "";
  return packs.find((item) => item.id === id);
}

export const TOOL_PACK_ROUTES: readonly StubRoute[] = [
  {
    method: "GET",
    pattern: /^\/tool-packs$/,
    handler: () => ({
      status: 200,
      body: { packs: packs.map(packDto), note: NOTE, unavailable_reason: null },
    }),
  },
  {
    method: "POST",
    pattern: /^\/tool-packs\/install$/,
    handler: (_url, body) => {
      const raw = (body ?? {}) as Record<string, unknown>;
      return submit(raw.manifest as Record<string, unknown>);
    },
  },
  {
    method: "POST",
    pattern: /^\/tool-packs\/[^/]+\/approve-update$/,
    handler: (url) => {
      const pack = findPack(url);
      if (pack === undefined) return { status: 404, body: { title: "ToolPack Not Found" } };
      if (pack.state === "REVOKED") {
        return { status: 409, body: { detail: `revoked tool pack cannot be updated: ${pack.id}` } };
      }
      if (pack.pending === null) {
        return { status: 409, body: { detail: `tool pack has no pending update: ${pack.id}` } };
      }
      const applied = replacePack({ ...pack, manifest: pack.pending, pending: null });
      return submitResult(200, "updated", { pack: applied, diff: null });
    },
  },
  {
    method: "POST",
    pattern: /^\/tool-packs\/[^/]+\/revoke$/,
    handler: (url, body) => {
      const reason = String(((body ?? {}) as Record<string, unknown>).reason ?? "");
      const pack = findPack(url);
      if (pack === undefined) return { status: 404, body: { title: "ToolPack Not Found" } };
      if (pack.state === "REVOKED") {
        return { status: 409, body: { detail: `tool pack already revoked: ${pack.id}` } };
      }
      const revoked = replacePack({
        ...pack,
        state: "REVOKED",
        pending: null,
        revoked_reason: reason,
      });
      return submitResult(200, "revoked", { pack: revoked, diff: null });
    },
  },
];
