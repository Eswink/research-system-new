/** 端点编辑表单的纯模型与校验（无 React 依赖，可单测）。 */

import type { LlmEndpointReadDto, LlmEndpointUpdateDto } from "../../api/types";

export interface EndpointFormState {
  name: string;
  baseUrl: string;
  apiStyle: "chat_completions" | "responses";
  enabled: boolean;
  timeout: string;
  retries: string;
  concurrency: string;
  apiKey: string;
}

export function endpointFormState(endpoint: LlmEndpointReadDto): EndpointFormState {
  return {
    name: endpoint.name,
    baseUrl: endpoint.base_url,
    apiStyle: endpoint.api_style === "responses" ? "responses" : "chat_completions",
    enabled: endpoint.enabled,
    timeout: String(endpoint.request_timeout_seconds),
    retries: String(endpoint.max_retries),
    concurrency: String(endpoint.concurrency_limit),
    apiKey: "",
  };
}

/** 校验并构建 PATCH 载荷；返回字符串表示校验消息。 */
export function toUpdatePayload(
  form: EndpointFormState,
  zh: boolean,
): LlmEndpointUpdateDto | string {
  const name = form.name.trim();
  const baseUrl = form.baseUrl.trim();
  const invalid = checkLimits({ form, name, baseUrl, zh });
  if (invalid !== null) return invalid;
  const payload: LlmEndpointUpdateDto = {
    name,
    base_url: baseUrl,
    api_style: form.apiStyle,
    enabled: form.enabled,
    request_timeout_seconds: Number(form.timeout),
    max_retries: Number(form.retries),
    concurrency_limit: Number(form.concurrency),
  };
  if (form.apiKey.length > 0) payload.api_key = form.apiKey;
  return payload;
}

function checkLimits(input: {
  form: EndpointFormState;
  name: string;
  baseUrl: string;
  zh: boolean;
}): string | null {
  const { form, name, baseUrl, zh } = input;
  const fail = (zhMsg: string, enMsg: string): string => (zh ? zhMsg : enMsg);
  if (name.length === 0) return fail("名称不能为空", "Name must not be empty");
  if (!/^https?:\/\/.+/.test(baseUrl)) {
    return fail("Base URL 必须为 http(s) 地址", "Base URL must be an http(s) URL");
  }
  const timeout = Number(form.timeout);
  if (!Number.isInteger(timeout) || timeout <= 0) {
    return fail("超时必须为正整数秒", "Timeout must be a positive integer of seconds");
  }
  const retries = Number(form.retries);
  if (!Number.isInteger(retries) || retries < 0) {
    return fail("重试次数必须为非负整数", "Retries must be a non-negative integer");
  }
  const concurrency = Number(form.concurrency);
  if (!Number.isInteger(concurrency) || concurrency <= 0) {
    return fail("并发上限必须为正整数", "Concurrency limit must be a positive integer");
  }
  return null;
}
