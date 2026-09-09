import { register } from "node:module";

// Node's structural/SSR unit tests have no CSS pipeline. Browser tests validate real styling.
register("./styleModuleLoader.mjs", import.meta.url);
