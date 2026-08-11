import type { ConcreteAdapter } from "../../../adapters/example/src/concrete-adapter.js";

export const bindConcreteAdapter = (adapter: ConcreteAdapter): string => adapter.kind;
