/**
 * Console e2e（EC-06 / PLAN-20260915-061）：项目删除语义。
 *
 * 验证"删除真的改变注册表"：无引用项目删除后从列表消失；有引用项目被后端 409
 * 拒绝并呈现引用清单（行保留）；默认项目是合成基线，不提供删除入口；删除活动
 * 项目后活动上下文回退到默认项目（不留下指向已删除 id 的悬空上下文）。
 */

import { expect, test, type Page } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";
import { resetProjectsStub } from "./stub-routes-projects";

const DEFAULT_PROJECT = "example-project";
const REFERENCED_PROJECT = "proj-funded-study";

test.beforeEach(() => {
  resetProjectsStub();
});

test.afterEach(() => {
  assertNoUnmatched();
});

async function openProjects(page: Page): Promise<void> {
  await stubApi(page);
  await page.goto("/#/portfolio/projects");
  await expect(page.getByTestId("projects-page")).toBeVisible();
  await expect(page.getByTestId("projects-list")).toBeVisible();
}

async function confirmDelete(page: Page, projectId: string): Promise<void> {
  await page.getByTestId(`project-delete-${projectId}`).click();
  await expect(page.getByRole("alertdialog")).toBeVisible();
  await page.getByTestId("confirm-dialog-confirm").click();
}

test("默认项目不提供删除入口（合成基线）", async ({ page }) => {
  await openProjects(page);
  await expect(page.getByTestId(`project-delete-${DEFAULT_PROJECT}`)).toBeDisabled();
  await expect(page.getByTestId(`project-delete-${DEFAULT_PROJECT}`)).toHaveAttribute(
    "title",
    "默认项目是合成基线，不提供删除",
  );
});

test("有引用的项目：删除被拒并呈现引用清单，行保留", async ({ page }) => {
  await openProjects(page);
  await confirmDelete(page, REFERENCED_PROJECT);

  const row = page.getByTestId(`project-row-${REFERENCED_PROJECT}`);
  await expect(row).toContainText("still references: runs=2, drafts=1");
  await expect(row).toBeVisible();
});

test("无引用项目：删除后从注册表消失", async ({ page }) => {
  await openProjects(page);
  await page.getByLabel("名称").fill("Transient Study");
  await page.getByRole("button", { name: "新建项目" }).click();
  await expect(page.getByTestId("project-row-proj-stub-1")).toBeVisible();

  await confirmDelete(page, "proj-stub-1");
  await expect(page.getByTestId("project-row-proj-stub-1")).toBeHidden();
  await expect(page.getByTestId(`project-row-${REFERENCED_PROJECT}`)).toBeVisible();
});

test("删除活动项目后活动上下文回退到默认项目", async ({ page }) => {
  await openProjects(page);
  await page.getByLabel("名称").fill("Active Study");
  await page.getByRole("button", { name: "新建项目" }).click();
  await page.getByTestId("project-switch-proj-stub-1").click();

  await expect(page.getByTestId("project-switcher")).toHaveValue("proj-stub-1");
  expect(await page.evaluate(() => window.localStorage.getItem("ros.active-project"))).toBe(
    "proj-stub-1",
  );

  await confirmDelete(page, "proj-stub-1");
  await expect(page.getByTestId("project-row-proj-stub-1")).toBeHidden();
  expect(await page.evaluate(() => window.localStorage.getItem("ros.active-project"))).toBe(
    DEFAULT_PROJECT,
  );
});
