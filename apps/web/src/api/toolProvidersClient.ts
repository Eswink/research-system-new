/** Tool Provider 目录只读客户端（PLAN-043 WP-B，EC-02）。 */

import { request } from "./http";
import type { ToolProviderListDto } from "./types";

export const toolProvidersClient = {
  list(): Promise<ToolProviderListDto> {
    return request("/tool-providers", { method: "GET" });
  },
};
