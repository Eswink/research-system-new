/** 策略面只读客户端（WP-C PLAN-049；声明规则 + 门链能力逐 scope 有效判决）。 */

import { request } from "./http";
import type { PolicyCapabilitiesDto } from "./types";

export const policyClient = {
  capabilities(): Promise<PolicyCapabilitiesDto> {
    return request("/policy/capabilities", { method: "GET" });
  },
};
