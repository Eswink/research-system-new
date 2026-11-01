/**
 * 链上制品的**人类可读标签**（GOAL-20261101-103 EC-04）。
 *
 * **它封住的失败形态**：`ArtifactBrowser` 把每个制品渲染成裸 id + 字节数 + media type。
 * GOAL-099/100/102 三轮做出来的手稿 / 应答信 / 编辑决定 / 投稿包五件，在 UI 上因此
 * **与一条 `tool-result:...` 没有区别** —— 用户知道"有制品"，但不知道"哪一份是手稿"。
 *
 * **判法（闭集 + 未命中不伪造）**：制品 id 的形态是 `{task_id}:{artifact_name}`
 * （`result_handler._artifact_for_output` 的命名约定），所以取 `:` 之后的**名字部分**
 * 在闭集里查。命中 ⇒ 给标签；未命中 ⇒ 返回 `null`，调用方**原样显示 id**。
 * 绝不"猜一个标签"—— 猜出来的标签比裸 id 更坏（它看起来像事实）。
 *
 * **只认名字，不认前缀**：`task_id` 是 UUID，不携带语义；唯一有语义的是名字部分。
 */

export interface ArtifactLabel {
  /** 中文标签（zh 语言下显示） */
  zh: string;
  /** 英文标签（en 语言下显示） */
  en: string;
}

/**
 * 闭集映射（**顺序无关**：按名字精确匹配，不做前缀匹配 / 不做模糊匹配）。
 *
 * 名字逐字取自各轮协议与装配器的真实产出名（`direction_to_manuscript_v1.yaml` 的
 * `outputs`、`report_task` 的装配清单、`submission_assembly` 的五件）。新增产物名时
 * 必须同步本表 —— 判据 `run-artifact-chain-labels.spec.ts` 钉住表里每一项都有对照。
 */
export const ARTIFACT_LABELS: Readonly<Record<string, ArtifactLabel>> = {
  research_question: { zh: "研究问题", en: "Research question" },
  retrieval_report: { zh: "检索报告", en: "Retrieval report" },
  novelty_claim: { zh: "创新点声明", en: "Novelty claim" },
  research_plan: { zh: "研究计划", en: "Research plan" },
  "experiment_result.json": { zh: "实验结果", en: "Experiment result" },
  metrics: { zh: "实验指标", en: "Metrics" },
  review_decision: { zh: "评审结论", en: "Review decision" },
  manuscript_narrative: { zh: "手稿正文", en: "Manuscript narrative" },
  "manuscript.md": { zh: "手稿", en: "Manuscript" },
  "manuscript_v2.md": { zh: "修改稿", en: "Revised manuscript" },
  editorial_decision: { zh: "编辑决定", en: "Editorial decision" },
  author_responses: { zh: "应答记录", en: "Author responses" },
  "response_letter.md": { zh: "应答信", en: "Response letter" },
  "cover_letter.md": { zh: "Cover Letter", en: "Cover letter" },
  "author_contributions.md": { zh: "作者贡献", en: "Author contributions" },
  "conflicts_of_interest.md": { zh: "利益冲突", en: "Conflicts of interest" },
  "data_availability.md": { zh: "数据可用性", en: "Data availability" },
  "supplementary.md": { zh: "补充材料", en: "Supplementary material" },
  "research_report.md": { zh: "研究报告", en: "Research report" },
};

/** 制品 id 的**名字部分**（`{task_id}:{name}` ⇒ `name`；没有 `:` ⇒ 原样）。 */
export function artifactName(artifactId: string): string {
  const index = artifactId.indexOf(":");
  return index === -1 ? artifactId : artifactId.slice(index + 1);
}

/**
 * 制品 id → 标签；**未命中 ⇒ `null`**（调用方原样显示 id，不伪造）。
 *
 * 注意入参可能是裸名字（live 读面偶尔直接给 `manuscript.md`）也可能是
 * `{task_id}:{name}` —— 两种形态都先取名字部分再查表。
 */
export function artifactLabel(artifactId: string): ArtifactLabel | null {
  return ARTIFACT_LABELS[artifactName(artifactId)] ?? null;
}

/** 语言选择（`zh` 之外一律按 en —— 本仓只有两种语言）。 */
export function labelText(label: ArtifactLabel, language: string): string {
  return language === "zh" ? label.zh : label.en;
}
