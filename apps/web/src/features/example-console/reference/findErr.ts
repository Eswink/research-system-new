import type * as E from "../exampleTypes";

/** Reference: screens/ProtocolEditor.sections.jsx; EXAMPLE ONLY. */
export const findErr = (errors: E.ProtocolIssue[], path: string) =>
  errors.find((e) => e.path === path);
