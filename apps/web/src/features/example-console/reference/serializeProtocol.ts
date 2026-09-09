import { stringify } from "yaml";
import type { Protocol } from "../exampleTypes";

/** Example document serialization is valid YAML, not the production ProtocolDefinition schema. */
export function serialize(protocol: Protocol): string {
  return stringify(protocol, { lineWidth: 100 });
}
