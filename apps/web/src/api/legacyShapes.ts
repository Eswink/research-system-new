/** 向后兼容的结果形状（ETag 资源）。 */

import type { LlmEndpointReadDto, Version } from "./types";

export interface EndpointWithEtag {
  dto: LlmEndpointReadDto;
  etag: Version;
}
