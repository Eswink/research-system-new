/** Tool Provider 目录只读客户端 + 注册治理写面（PLAN-043 WP-B EC-02；PLAN-060 EC-05）。
 *
 * 写面约束与主 client 一致：mutating 带 Idempotency-Key；服务端返回的
 * `catalog_active` 表示该注册是否已进入目录（PENDING/REVOKED 都是 false）。
 */

import { newIdempotencyKey, request } from "./http";
import type {
  ToolProviderListDto,
  ToolProviderRegisterDto,
  ToolProviderRegistrationDto,
  ToolProviderRegistrationListDto,
  ToolProviderUpdateDto,
} from "./types";

function registrationPath(providerId: string, action?: string): string {
  const base = `/tool-provider-registrations/${encodeURIComponent(providerId)}`;
  return action === undefined ? base : `${base}/${action}`;
}

export const toolProvidersClient = {
  list(): Promise<ToolProviderListDto> {
    return request("/tool-providers", { method: "GET" });
  },
  registrations(): Promise<ToolProviderRegistrationListDto> {
    return request("/tool-provider-registrations", { method: "GET" });
  },
  register(payload: ToolProviderRegisterDto): Promise<ToolProviderRegistrationDto> {
    return request(
      "/tool-provider-registrations",
      { method: "POST", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  updateRegistration(
    providerId: string,
    payload: ToolProviderUpdateDto,
  ): Promise<ToolProviderRegistrationDto> {
    return request(
      registrationPath(providerId),
      { method: "PATCH", body: JSON.stringify(payload) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  approveRegistration(providerId: string): Promise<ToolProviderRegistrationDto> {
    return request(
      registrationPath(providerId, "approve"),
      { method: "POST" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  revokeRegistration(providerId: string, reason: string): Promise<ToolProviderRegistrationDto> {
    return request(
      registrationPath(providerId, "revoke"),
      { method: "POST", body: JSON.stringify({ reason }) },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
  healthCheckRegistration(providerId: string): Promise<ToolProviderRegistrationDto> {
    return request(
      registrationPath(providerId, "health-check"),
      { method: "POST" },
      { idempotencyKey: newIdempotencyKey() },
    );
  },
};
