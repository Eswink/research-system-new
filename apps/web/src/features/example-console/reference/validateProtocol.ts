import type { Protocol, ProtocolIssue } from "../exampleTypes";
import { budgetChecks, fieldChecks, objectiveChecks } from "../protocolChecks";

/** This visual editor validates only the example document, never a production RunManifest. */
export function validate(protocol: Protocol) {
  const issues: ProtocolIssue[] = [
    ...fieldChecks(protocol),
    ...objectiveChecks(protocol),
    ...budgetChecks(protocol),
  ];
  return {
    errors: issues.filter((issue) => issue.severity === "error"),
    warnings: issues.filter((issue) => issue.severity === "warning"),
  };
}
