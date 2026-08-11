import type { ApplicationRequest } from "../../application/src/request.js";
import { randomUUID } from "node:crypto";

export type InvalidDomainState = Readonly<{
  request: ApplicationRequest;
  runtimeId: string;
}>;

export const createInvalidDomainState = (request: ApplicationRequest): InvalidDomainState => ({
  request,
  runtimeId: randomUUID(),
});
