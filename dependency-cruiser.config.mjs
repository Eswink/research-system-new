const fixtureRoot = "^tests/architecture/typescript/fixtures/(?:valid|invalid)/";
const domain = `${fixtureRoot}packages/domain/`;
const application = `${fixtureRoot}packages/application/`;
const adapters = `${fixtureRoot}adapters/`;
const entries = `${fixtureRoot}(?:apps|services)/`;
const production = `${fixtureRoot}(?:apps|services|packages|adapters)/`;

export default {
  forbidden: [
    {
      name: "no-circular",
      severity: "error",
      from: {},
      to: { circular: true },
    },
    {
      name: "not-to-unresolvable",
      severity: "error",
      from: {},
      to: { couldNotResolve: true },
    },
    {
      name: "domain-not-to-outer-layers",
      severity: "error",
      from: { path: domain },
      to: { path: `${fixtureRoot}(?:packages/application|adapters|services|apps)/` },
    },
    {
      name: "domain-not-to-provider-or-runtime",
      severity: "error",
      from: { path: domain },
      to: { dependencyTypes: ["core", "npm", "npm-dev", "npm-optional", "npm-peer"] },
    },
    {
      name: "application-not-to-outer-layers",
      severity: "error",
      from: { path: application },
      to: { path: `${fixtureRoot}(?:adapters|services|apps)/` },
    },
    {
      name: "entry-not-to-domain",
      severity: "error",
      from: { path: entries },
      to: { path: domain },
    },
    {
      name: "adapter-not-to-entry",
      severity: "error",
      from: { path: adapters },
      to: { path: entries },
    },
    {
      name: "production-not-to-test-support",
      severity: "error",
      from: { path: production },
      to: { path: `${fixtureRoot}test-support/` },
    },
  ],
  options: {
    doNotFollow: {
      dependencyTypes: ["core", "npm", "npm-dev", "npm-optional", "npm-peer"],
    },
    tsConfig: { fileName: "tsconfig.base.json" },
    tsPreCompilationDeps: true,
  },
};
