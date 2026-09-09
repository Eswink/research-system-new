import { createContext } from "react";
import type { DataSource, SourceSelection } from "./presentationPolicy";

export interface PresentationContextValue {
  source: DataSource;
  selection: SourceSelection;
  setSource: (source: SourceSelection) => void;
  reason: string;
}

export const PresentationContext = createContext<PresentationContextValue>({
  source: "live",
  selection: "auto",
  setSource: () => undefined,
  reason: "",
});
