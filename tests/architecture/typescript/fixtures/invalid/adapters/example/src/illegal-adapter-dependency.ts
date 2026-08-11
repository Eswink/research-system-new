import { bypassApplication } from "../../../services/example/src/bypass-application.js";
import { missingDependency } from "./missing-dependency.js";

export const illegalAdapterDependency = `${bypassApplication}:${missingDependency}`;
