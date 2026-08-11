import type { InvalidDomainState } from "../../../packages/domain/src/invalid-domain-state.js";
import { testOnlyValue } from "../../../test-support/src/test-only-value.js";

export const bypassApplication = (state: InvalidDomainState): string =>
  `${state.runtimeId}:${testOnlyValue}`;
