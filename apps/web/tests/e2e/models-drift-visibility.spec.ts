/**
 * 漂移三态读面（GOAL-20260920-008 EC-05 / PLAN-20260920-117 WP-C）。
 *
 * 判据的要点是**三态互不混淆**，尤其是 `UNKNOWN`：
 * 「没探到」若被渲染成「一致」，就等于把「无法证明」说成「已证明」（AGENTS.md §4）。
 * 所以这里逐态断言文案，并显式断言 `UNKNOWN` 那一屏**不得**出现「一致 / match」的口径。
 *
 * 拒绝态（probe 失败 ⇒ returned_model_name=null）是 `UNKNOWN` 的真实来源之一；
 * 另外两态用替身注入「同名 / 异名」两种响应。
 */

import { expect, test, type Page } from "@playwright/test";

import { MODEL } from "./apiFixtures";
import { stubApi } from "./stub-api";

interface DriftPayload {
  state: "MATCH" | "DRIFT" | "UNKNOWN";
  returned: string | null;
  detail: string;
}

/** 显式选语言：诚实文案是本地化字符串，断言必须先钉住渲染语言。 */
async function seedLanguage(page: Page, language: "en" | "zh"): Promise<void> {
  await page.addInitScript((lang) => {
    localStorage.setItem(
      "ros.console.preferences",
      JSON.stringify({
        theme: "dark",
        density: "normal",
        language: lang,
        editorMode: "form",
        version: "test",
      }),
    );
  }, language);
}

async function stubProbe(page: Page, payload: DriftPayload): Promise<void> {
  await page.route("**/api/models/*/probe", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        model_id: MODEL.id,
        ok: payload.state !== "UNKNOWN",
        observed_capabilities: [],
        returned_model_name: payload.returned,
        system_fingerprint: payload.state === "MATCH" ? "fp_1" : null,
        provider_fingerprint_available: payload.state === "MATCH",
        drift: {
          state: payload.state,
          declared_model_name: MODEL.model_name,
          returned_model_name: payload.returned,
          detail: payload.detail,
        },
        error_category: payload.state === "UNKNOWN" ? "CONFIGURATION" : null,
        error_message_redacted: null,
        capability_failures: [],
        probed_at: "2026-09-10T00:00:00Z",
        fingerprint: null,
      }),
    }),
  );
}

/** 选中模型 → 点 Probe → 在确认框里确认（真实探测必须显式确认，判据也跟着走一遍）。 */
async function openModelAndProbe(page: Page, zh: boolean): Promise<void> {
  await page.goto("/#/library/model-registry");
  await expect(page.getByTestId("models-page")).toBeVisible();
  await page.getByRole("row", { name: new RegExp(MODEL.model_name) }).click();
  await page.getByRole("button", { name: "Probe", exact: true }).click();
  await page.getByRole("button", { name: zh ? "执行探测" : "Run probe" }).click();
  await expect(page.getByTestId("probe-drift")).toBeVisible();
}

test.beforeEach(async ({ page }) => {
  await stubApi(page);
  await page.route("**/api/models", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([MODEL]),
    }),
  );
  await page.route(`**/api/models/${MODEL.id}`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MODEL),
    }),
  );
  await page.route(`**/api/models/${MODEL.id}/compatibility`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        model: MODEL,
        endpoint_id: MODEL.endpoint_id,
        endpoint_healthy_hint: null,
        hard_capability_requirements: [],
      }),
    }),
  );
});

test("一致：声明值与返回标识相符", async ({ page }) => {
  await seedLanguage(page, "en");
  await stubProbe(page, {
    state: "MATCH",
    returned: MODEL.model_name,
    detail: `declared and returned agree on '${MODEL.model_name}'`,
  });
  await openModelAndProbe(page, false);
  const drift = page.getByTestId("probe-drift");
  await expect(drift).toHaveAttribute("data-drift-state", "MATCH");
  await expect(drift).toContainText("Match");
});

test("漂移：点名声明值与返回标识两个值", async ({ page }) => {
  await seedLanguage(page, "en");
  await stubProbe(page, {
    state: "DRIFT",
    returned: "agnes-2.5-pro",
    detail: `declared '${MODEL.model_name}' but provider returned 'agnes-2.5-pro'`,
  });
  await openModelAndProbe(page, false);
  const drift = page.getByTestId("probe-drift");
  await expect(drift).toHaveAttribute("data-drift-state", "DRIFT");
  await expect(drift).toContainText(MODEL.model_name);
  await expect(drift).toContainText("agnes-2.5-pro");
});

test("未知：未探到必须自带反义，不得显示为一致", async ({ page }) => {
  await seedLanguage(page, "en");
  await stubProbe(page, {
    state: "UNKNOWN",
    returned: null,
    detail: `declared '${MODEL.model_name}'; provider did not return a model identifier`,
  });
  await openModelAndProbe(page, false);
  const drift = page.getByTestId("probe-drift");
  await expect(drift).toHaveAttribute("data-drift-state", "UNKNOWN");
  await expect(drift).toContainText("unknown is not the same as no drift");
  // 反向断言：未知那一屏不得出现「一致」口径。
  await expect(drift).not.toContainText("Match");
  await expect(drift).not.toContainText("agree");
});

test("未知：中文读面同样明写「未知不等于无漂移」", async ({ page }) => {
  await seedLanguage(page, "zh");
  await stubProbe(page, {
    state: "UNKNOWN",
    returned: null,
    detail: `declared '${MODEL.model_name}'; provider did not return a model identifier`,
  });
  await openModelAndProbe(page, true);
  const drift = page.getByTestId("probe-drift");
  await expect(drift).toContainText("未知不等于无漂移");
});
