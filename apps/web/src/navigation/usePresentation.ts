import { useContext } from "react";
import { PresentationContext } from "./presentationContext";

export function usePresentation() {
  return useContext(PresentationContext);
}
