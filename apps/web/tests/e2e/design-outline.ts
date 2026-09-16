/**
 * 结构签名（DOM outline）——设计门禁的第二判据（GOAL-20260915-003 EC-01）。
 *
 * 为什么需要它：`maxDiffPixelRatio: 0.02` 对**整块新增**不敏感——cycle 3/5/6/7
 * 实测分别只差 1.73% / 1.02%·0.93% / 0.79%·0.66% / 0.48%·0.47%，全部低于阈值，
 * 门禁不报警，只能靠"流程要求人工重生成基线"兜底。像素比率衡量的是"变了多少
 * 面积"，结构签名衡量的是"多了/少了哪些节点"：一行新面板会让签名立刻不同，
 * 与它占多大面积无关。
 *
 * 签名只取**跨平台稳定**的结构性身份（标签 / testid / role / aria-label / 叶子文本 /
 * 子节点数），不取 CSS-module 哈希类名、不取样式、不取坐标——那些要么随构建漂移，
 * 要么是像素判据的职责。易变字面量（ISO 时间戳、长数字串、UUID）先归一化再入签名。
 */

import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { expect, type Page } from "@playwright/test";

const ISO_TIMESTAMP = /\d{4}-\d{2}-\d{2}[T ][0-9:.]+(?:[+-]\d{2}:\d{2}|Z)?/g;
const CLOCK_TIME = /\b\d{1,2}:\d{2}(?::\d{2})?\b/g;
const UUID = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi;
const LONG_DIGITS = /\d{6,}/g;
const TEXT_LIMIT = 120;

/** 归一化易变字面量：时间戳 / 时钟 / UUID / 长数字串 / 空白。 */
export function normalizeText(raw: string): string {
  return raw
    .replace(ISO_TIMESTAMP, "<ts>")
    .replace(UUID, "<uuid>")
    .replace(CLOCK_TIME, "<clock>")
    .replace(LONG_DIGITS, "<n>")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, TEXT_LIMIT);
}

interface OutlineNode {
  tag: string;
  testid: string | null;
  role: string | null;
  label: string | null;
  text: string;
  children: number;
}

/**
 * 浏览器侧遍历：只读，返回扁平的前序节点表（在 `page.evaluate` 里执行）。
 *
 * 注意这个函数体会被序列化进浏览器，不能引用模块作用域的常量。
 */
function collectNodes(): OutlineNode[] {
  const skip = new Set(["SCRIPT", "STYLE", "LINK", "META", "NOSCRIPT", "TEMPLATE", "HEAD"]);
  const nodes: OutlineNode[] = [];
  const walk = (element: Element): void => {
    const children = Array.from(element.children).filter(
      (child) => !skip.has(child.tagName.toUpperCase()),
    );
    const own = Array.from(element.childNodes)
      .filter((node) => node.nodeType === Node.TEXT_NODE)
      .map((node) => node.textContent ?? "")
      .join(" ");
    nodes.push({
      tag: element.tagName.toLowerCase(),
      testid: element.getAttribute("data-testid"),
      role: element.getAttribute("role"),
      label: element.getAttribute("aria-label"),
      text: own,
      children: children.length,
    });
    for (const child of children) {
      walk(child);
    }
  };
  walk(document.body);
  return nodes;
}

function describe(node: OutlineNode): string {
  const parts: string[] = [node.tag];
  if (node.testid !== null) parts.push(`testid=${node.testid}`);
  if (node.role !== null) parts.push(`role=${node.role}`);
  if (node.label !== null) parts.push(`label=${node.label}`);
  parts.push(`kids=${String(node.children)}`);
  const text = normalizeText(node.text);
  return text === "" ? parts.join(" ") : `${parts.join(" ")} | ${text}`;
}

/** 读取当前页面的结构签名（确定性：同一 DOM 必得同一字符串）。 */
export async function buildOutline(page: Page): Promise<string> {
  const nodes = await page.evaluate(collectNodes);
  return nodes.map(describe).join("\n");
}

/**
 * 基线存放：**单一 JSON**（不是 Playwright 的 per-platform 快照）。
 *
 * 结构签名是平台无关的（只有标签/testid/role/文本，没有字体与像素），因此不该像
 * 截图那样维护 win32/linux 两份；放一个文件也便于在 code review 里逐行看 diff。
 * 更新方式：`UPDATE_OUTLINES=1` 跑一次用例（等价于 `--update-snapshots`）。
 */
export const OUTLINE_STORE = join(import.meta.dirname, "design-outlines.json");

export function loadOutlines(): Record<string, string> {
  return JSON.parse(readFileSync(OUTLINE_STORE, "utf8")) as Record<string, string>;
}

function saveOutlines(outlines: Record<string, string>): void {
  const entries = Object.entries(outlines).sort(([a], [b]) => a.localeCompare(b));
  writeFileSync(OUTLINE_STORE, `${JSON.stringify(Object.fromEntries(entries), null, 2)}\n`, "utf8");
}

/**
 * 逐路由比对结构签名；`UPDATE_OUTLINES=1` 时改写基线（**CI 不设该变量**，
 * 与 `--update-snapshots` 同理：更新是显式的本地意图，不是自动降级）。
 */
export function assertOutlines(observed: Record<string, string>): void {
  const stored = loadOutlines();
  if (process.env.UPDATE_OUTLINES === "1") {
    saveOutlines({ ...stored, ...observed });
    return;
  }
  const added = Object.keys(observed).filter((name) => stored[name] === undefined);
  const stale = Object.keys(stored).filter((name) => observed[name] === undefined);
  const drifted = Object.entries(observed)
    .filter(([name, outline]) => stored[name] !== outline)
    .map(([name]) => name);
  expect(added, "结构签名基线缺少这些路由（UPDATE_OUTLINES=1 生成）").toEqual([]);
  expect(stale, "结构签名基线含已不存在的路由（路由删除时基线同步删除）").toEqual([]);
  expect(
    drifted,
    "结构签名漂移：节点增删会命中此判据（GOAL-003 EC-01）；确认改动后 UPDATE_OUTLINES=1 重生成",
  ).toEqual([]);
}
