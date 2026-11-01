import type { ArtifactDto } from "../../api/types";
import { api } from "../../api/client";
import { PanelSection } from "../../components/PanelSection";
import { EmptyState, LoadingState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";
import { artifactName } from "../workspace/artifactLabels";

/**
 * 手稿链视图（GOAL-20261101-103 EC-04）。
 *
 * **它补哪一格**：`ReportsPage` 此前只渲染 M12 的 `deliverable.json`；GOAL-099/100/102
 * 做出来的 `manuscript.md` / `manuscript_v2.md` / `editorial_decision` / 投稿包五件
 * **完全不在页面上**。于是"系统写了一篇能投出去的稿"这件事，用户只能靠 curl 才知道。
 *
 * **三条判据口径**：
 *
 * 1. `manuscript.md` 在场 ⇒ 渲染它的 **Markdown 正文**（不是裸 id、不是 JSON）；
 * 2. `editorial_decision` 在场 ⇒ 把它按 `EditorialDecisionDto` 解出来显示四值之一 + 理由
 *    + 要求的改动（**解不出来就如实说要人工看**，不猜）；
 * 3. 投稿包五件在场 ⇒ 每件一个可下载链接（用 `artifactContentUrl`，与 ArtifactBrowser
 *    同一个下载面 —— 不另开一条取内容的通道）。
 *
 * **没有手稿 ⇒ 不渲染本面板**（由调用方判）；`manuscript_v2.md` 在场时**两份都列**：
 * 改稿链的意义就在于"能对照"，只显示最新版会让 supersedes 这条结构事实在 UI 上消失。
 */

/** 手稿链上会被本面板呈现的制品名（闭集；未命中的制品不进本面板）。 */
const CHAIN_NAMES = [
  "manuscript.md",
  "manuscript_v2.md",
  "editorial_decision",
  "cover_letter.md",
  "author_contributions.md",
  "conflicts_of_interest.md",
  "data_availability.md",
  "supplementary.md",
  "response_letter.md",
] as const;

/** 投稿包五件（与 `submission_assembly` 的装配清单逐字对应）。 */
const PACKAGE_NAMES = new Set([
  "cover_letter.md",
  "author_contributions.md",
  "conflicts_of_interest.md",
  "data_availability.md",
  "supplementary.md",
]);

export function hasManuscript(artifacts: ArtifactDto[]): boolean {
  return artifacts.some((artifact) => artifactName(artifact.id) === "manuscript.md");
}

/** 按名字取制品（同名多件时取**最后**一件 —— 与"后落的事实更完整"同一条口径）。 */
function findByName(artifacts: ArtifactDto[], name: string): ArtifactDto | null {
  const matched = artifacts.filter((artifact) => artifactName(artifact.id) === name);
  return matched.length === 0 ? null : (matched[matched.length - 1] ?? null);
}

/** 收齐「名字 → 制品」对，**丢掉没在场的那几件**（不补占位）。 */
function present(
  artifacts: ArtifactDto[],
  names: readonly string[],
): { name: string; artifact: ArtifactDto }[] {
  const rows: { name: string; artifact: ArtifactDto }[] = [];
  for (const name of names) {
    const artifact = findByName(artifacts, name);
    if (artifact !== null) rows.push({ name, artifact });
  }
  return rows;
}

export function ManuscriptPanel({ artifacts }: { artifacts: ArtifactDto[] }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const manuscript = findByName(artifacts, "manuscript.md");
  if (manuscript === null) return null;
  return (
    <>
      <ManuscriptSection artifact={manuscript} zh={zh} title={zh ? "手稿" : "Manuscript"} />
      <RevisionSection artifacts={artifacts} zh={zh} />
      <DecisionSection artifacts={artifacts} zh={zh} />
      <PackageSection artifacts={artifacts} zh={zh} />
    </>
  );
}

/** 一份手稿（正文 + 下载）。标题可换（手稿 / 修改稿）。 */
function ManuscriptSection({
  artifact,
  zh,
  title,
  note,
}: {
  artifact: ArtifactDto;
  zh: boolean;
  title: string;
  note?: string;
}) {
  return (
    <PanelSection
      title={title}
      extra={
        <a className="btn sm" href={api.artifactContentUrl(artifact.id)} download={artifact.id}>
          {zh ? "下载" : "Download"}
        </a>
      }
    >
      {note !== undefined && (
        <KeyValueList fields={[{ label: note, value: artifact.supersedes ?? "—" }]} />
      )}
      <ManuscriptBody artifactId={artifact.id} zh={zh} />
    </PanelSection>
  );
}

/** 修改稿（改稿链）：在场才渲染；父指针显式显示 ⇒ `supersedes` 这条结构事实在 UI 上可见。 */
function RevisionSection({ artifacts, zh }: { artifacts: ArtifactDto[]; zh: boolean }) {
  const revision = findByName(artifacts, "manuscript_v2.md");
  if (revision === null) return null;
  return (
    <ManuscriptSection
      artifact={revision}
      zh={zh}
      title={zh ? "修改稿（改稿链）" : "Revised manuscript (revision chain)"}
      note={zh ? "替代" : "Supersedes"}
    />
  );
}

/** 编辑决定块（在场才渲染）。 */
function DecisionSection({ artifacts, zh }: { artifacts: ArtifactDto[]; zh: boolean }) {
  const decision = findByName(artifacts, "editorial_decision");
  if (decision === null) return null;
  return <EditorialDecisionBlock artifactId={decision.id} zh={zh} />;
}

/** 投稿包五件 + 链上其余材料（每条一个下载链接）。 */
function PackageSection({ artifacts, zh }: { artifacts: ArtifactDto[]; zh: boolean }) {
  const rows = present(artifacts, [
    ...PACKAGE_NAMES,
    ...CHAIN_NAMES.filter(
      (name) =>
        !PACKAGE_NAMES.has(name) &&
        name !== "manuscript.md" &&
        name !== "manuscript_v2.md" &&
        name !== "editorial_decision",
    ),
  ]);
  if (rows.length === 0) return null;
  return (
    <PanelSection title={zh ? "投稿包与链上材料" : "Submission package and chain material"}>
      <ul className={styles.list} data-testid="submission-package-links">
        {rows.map((item) => (
          <li key={item.name}>
            <a className="btn sm ghost" href={api.artifactContentUrl(item.artifact.id)} download>
              {item.name}
            </a>
          </li>
        ))}
      </ul>
    </PanelSection>
  );
}

/** 制品正文（逐字渲染；Markdown 按等宽块呈现，不引入解析依赖）。 */
function ManuscriptBody({ artifactId, zh }: { artifactId: string; zh: boolean }) {
  const text = useResource(`manuscript-body:${artifactId}`, () =>
    api.artifactPreviewText(artifactId),
  );
  return (
    <div data-testid="manuscript-body">
      {text.phase === "loading" && <LoadingState message={zh ? "加载正文…" : "Loading…"} />}
      {text.error !== null && <EmptyState message={text.error} />}
      {text.data !== null && <pre className={styles.code}>{text.data}</pre>}
    </div>
  );
}

/**
 * 编辑决定块（`EditorialDecisionDto` 的四个取值 + 理由 + 要求的改动）。
 *
 * **解不出来就说解不出来**：决定块是模型写的 JSON；畸形时显示"内容不是可解析的决定块"
 * 并保留下载链接 —— **不**猜一个 `decision`（猜出来的判定比没有更坏）。
 */
function EditorialDecisionBlock({ artifactId, zh }: { artifactId: string; zh: boolean }) {
  const text = useResource(`editorial-decision:${artifactId}`, () =>
    api.artifactPreviewText(artifactId),
  );
  return (
    <PanelSection title={zh ? "编辑决定" : "Editorial decision"}>
      <div data-testid="editorial-decision-block">
        {text.phase === "loading" && <LoadingState message={zh ? "加载…" : "Loading…"} />}
        {text.data !== null && <ParsedDecision raw={text.data} zh={zh} artifactId={artifactId} />}
      </div>
    </PanelSection>
  );
}

const DECISIONS = new Set(["accept", "minor_revision", "major_revision", "reject"]);

function ParsedDecision({ raw, zh, artifactId }: { raw: string; zh: boolean; artifactId: string }) {
  const parsed = parseDecision(raw);
  if (parsed === null) {
    return (
      <div data-testid="editorial-decision-unparsed">
        <EmptyState
          message={
            zh
              ? "内容不是可解析的决定块（需人工阅读原文）"
              : "The content is not a parsable decision block (read the raw text)"
          }
        />
        <a className="btn sm" href={api.artifactContentUrl(artifactId)} download>
          {zh ? "下载原文" : "Download raw"}
        </a>
      </div>
    );
  }
  return (
    <>
      <KeyValueList
        fields={[
          { label: zh ? "决定" : "Decision", value: parsed.decision },
          { label: zh ? "理由" : "Rationale", value: parsed.rationale },
          {
            label: zh ? "目标期刊" : "Target journal",
            value: parsed.target_journal ?? "—",
          },
        ]}
      />
      {parsed.required_changes.length > 0 && (
        <ol data-testid="editorial-required-changes">
          {parsed.required_changes.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      )}
    </>
  );
}

interface ParsedEditorialDecision {
  decision: string;
  rationale: string;
  required_changes: string[];
  target_journal: string | null;
}

/**
 * 决定块的解析（**两种输入形态都认**，与后端 `parse_editorial_decision` 同一纪律）：
 * 直形态（顶层就是 `editorial_decision` 块）与信封形态（正文里一段 ```json 围栏）。
 * 取值不在四值闭集里 ⇒ `null`（交回"不可解析"，不猜）。
 */
export function parseDecision(raw: string): ParsedEditorialDecision | null {
  const candidates: string[] = [];
  const fenced = /```json\s*([\s\S]*?)```/g;
  for (let match = fenced.exec(raw); match !== null; match = fenced.exec(raw)) {
    candidates.push(match[1] ?? "");
  }
  candidates.push(raw);
  for (const candidate of candidates) {
    const block = editorialBlock(candidate);
    if (block === null) continue;
    const decision = block.decision;
    if (typeof decision !== "string" || !DECISIONS.has(decision)) continue;
    const rationale = typeof block.rationale === "string" ? block.rationale : "";
    const changes = Array.isArray(block.required_changes)
      ? block.required_changes.filter((item): item is string => typeof item === "string")
      : [];
    const journal = typeof block.target_journal === "string" ? block.target_journal : null;
    return { decision, rationale, required_changes: changes, target_journal: journal };
  }
  return null;
}

function editorialBlock(text: string): Record<string, unknown> | null {
  try {
    const parsed: unknown = JSON.parse(text);
    if (typeof parsed !== "object" || parsed === null) return null;
    const outer = parsed as Record<string, unknown>;
    const inner = outer.editorial_decision;
    if (typeof inner === "object" && inner !== null) return inner as Record<string, unknown>;
    return outer;
  } catch {
    return null;
  }
}
