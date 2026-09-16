/**
 * 结构签名判据的反证（GOAL-003 EC-01 / PLAN-20260915-063）。
 *
 * 判据存在的理由是"整块新增内容"在像素判据下不会被报警（实测 0.48%~1.73% < 2%）。
 * 因此这里不重复"跑一遍 33 路由"（那是 design-fidelity 的职责），而是证明判据**会咬**：
 *  ① 注入一个额外面板 → 判据失败；
 *  ② 删除一个已有节点行 → 判据失败；
 *  ③ 只改样式（颜色）→ 判据不失败（避免把门禁变成噪音）；
 *  ④ 易变字面量（时间戳/UUID/长数字）被归一化，不会制造假漂移。
 *
 * 另：同一注入同时截两张图落到 `test-results/outline-guard/`，供
 * `scratch/outline-vs-pixel/measure.py` 量化"像素判据在同一改动上差多少"，
 * 作为"为什么需要第二判据"的对照证据。
 */

import { expect, test, type Page } from "@playwright/test";

import { assertOutlines, buildOutline, loadOutlines, normalizeText } from "./design-outline";
import { stubApi } from "./stub-api";

/** 基线 key（对应 design-fidelity 的 route.name）与真实 hash 是两件事。 */
const ROUTE = "portfolio-projects";
const HASH = "#/portfolio/projects";
const SHOT_DIR = "test-results/outline-guard";

async function openProjects(page: Page): Promise<void> {
  await stubApi(page);
  await page.goto(`/${HASH}`);
  await expect(page.getByTestId("projects-page")).toBeVisible();
}

/**
 * 模拟"整块新增"：一个带 testid 的面板 + 两个子节点（含一条新列表行）。
 *
 * `target` = "viewport" 时插到内容区顶部（可见，用于与像素判据做对照实验）；
 * "offscreen" 时挂到 body 末尾（落在视口之外——结构判据仍应看得到它，
 * 像素判据则完全看不见）。
 */
async function injectPanel(page: Page, target: "viewport" | "offscreen"): Promise<void> {
  await page.evaluate((where) => {
    const panel = document.createElement("section");
    panel.setAttribute("data-testid", "injected-panel");
    panel.setAttribute("role", "region");
    panel.setAttribute("aria-label", "注入面板");
    panel.innerHTML = [
      "<h2>Regenerated Evidence</h2>",
      "<ul><li data-testid='injected-row'>row-one</li></ul>",
    ].join("");
    const main = document.querySelector("main");
    if (where === "viewport" && main !== null) {
      main.prepend(panel);
      return;
    }
    document.body.append(panel);
  }, target);
}

/** 模型化的"已有节点消失"：从签名里移除一行（等价于页面少了一个节点）。 */
function dropOneLine(outline: string): string {
  const lines = outline.split("\n");
  return [...lines.slice(0, 5), ...lines.slice(6)].join("\n");
}

test("反证：注入可见面板 → 结构签名判据失败（并留下像素对照截图）", async ({ page }) => {
  await openProjects(page);
  const before = await buildOutline(page);
  await page.screenshot({ path: `${SHOT_DIR}/panel-before.png` });
  await injectPanel(page, "viewport");
  await page.screenshot({ path: `${SHOT_DIR}/panel-after.png` });
  const after = await buildOutline(page);

  expect(after, "注入后结构签名必须变化").not.toBe(before);
  expect(after).toContain("testid=injected-panel");
  const stored = loadOutlines();
  expect(
    () => {
      assertOutlines({ ...stored, [ROUTE]: after });
    },
    "同一注入必须让判据函数失败（否则门禁形同虚设）",
  ).toThrow(/结构签名漂移/);
});

test("反证：视口外的节点同样改变签名（判据不只看视口）", async ({ page }) => {
  await openProjects(page);
  const before = await buildOutline(page);
  await page.screenshot({ path: `${SHOT_DIR}/offscreen-before.png` });
  await injectPanel(page, "offscreen");
  await page.screenshot({ path: `${SHOT_DIR}/offscreen-after.png` });
  const after = await buildOutline(page);

  // 追加到 body 末尾 → 落在视口之外：截图看不到，DOM 看得到。
  expect(after, "视口外的注入仍然改变签名").not.toBe(before);
  expect(after).toContain("testid=injected-panel");
  expect(
    () => {
      assertOutlines({ ...loadOutlines(), [ROUTE]: after });
    },
    "视口外的新增节点也必须判红",
  ).toThrow(/结构签名漂移/);
});

test("反证：列表多一行 → 结构签名判据失败（最贴近 cycle 7 的真实改动）", async ({ page }) => {
  await openProjects(page);
  const before = await buildOutline(page);
  await page.screenshot({ path: `${SHOT_DIR}/row-before.png` });
  await page.evaluate(() => {
    const list = document.querySelector("[data-testid='projects-list']");
    const row = document.createElement("li");
    row.setAttribute("data-testid", "row-injected-project");
    row.textContent = "Transient Study · proj-stub-9";
    list?.append(row);
  });
  await page.screenshot({ path: `${SHOT_DIR}/row-after.png` });
  const after = await buildOutline(page);

  expect(after, "多一行必须改变签名").not.toBe(before);
  expect(after).toContain("testid=row-injected-project");
  expect(
    () => {
      assertOutlines({ ...loadOutlines(), [ROUTE]: after });
    },
    "多一行也必须判红（这正是 cycle 7 只差 0.48% 的那种改动）",
  ).toThrow(/结构签名漂移/);
});

test("反证：节点消失 → 结构签名判据失败", async ({ page }) => {
  await openProjects(page);
  const stored = loadOutlines();
  const reduced = dropOneLine(stored[ROUTE] ?? "");
  expect(reduced).not.toBe(stored[ROUTE]);
  expect(
    () => {
      assertOutlines({ ...stored, [ROUTE]: reduced });
    },
    "少一个节点同样必须判红（判据不只对新增敏感）",
  ).toThrow(/结构签名漂移/);
});

test("对照：只改样式（颜色）→ 判据不误报", async ({ page }) => {
  await openProjects(page);
  const before = await buildOutline(page);
  await page.evaluate(() => {
    for (const row of document.querySelectorAll("li")) {
      (row as HTMLElement).style.backgroundColor = "rgb(12, 34, 56)";
    }
  });
  const styled = await buildOutline(page);

  expect(styled, "纯样式变化不应改变结构签名").toBe(before);
  const stored = loadOutlines();
  expect(() => {
    assertOutlines({ ...stored, [ROUTE]: styled });
  }).not.toThrow();
});

test("易变字面量归一化：时间戳/UUID/长数字不制造假漂移", () => {
  expect(normalizeText("run 0199123456789 ok")).toBe("run <n> ok");
  expect(normalizeText("at 2026-09-16T00:00:00+00:00 done")).toBe("at <ts> done");
  expect(normalizeText("id 3f2504e0-4f89-41d3-9a0c-0305e82c3301")).toBe("id <uuid>");
  expect(normalizeText("  多   空格\t换行\n也要归一  ")).toBe("多 空格 换行 也要归一");
});
