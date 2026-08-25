const fixtureRoot = "^tests/architecture/typescript/fixtures/(?:valid|invalid)/";
const productionRoot = "^";
const fixtureExclusion = "^(?!.*/tests/architecture/typescript/fixtures/).*$";

function layerRules(prefix, excludeFixtures) {
  const from = (path) => (excludeFixtures ? { path, pathNot: fixtureExclusion } : { path });
  const to = (path) => (excludeFixtures ? { path, pathNot: fixtureExclusion } : { path });
  const domain = `${prefix}packages/domain/`;
  const application = `${prefix}packages/application/`;
  const adapters = `${prefix}adapters/`;
  const entries = `${prefix}(?:apps|services)/`;
  const production = `${prefix}(?:apps|services|packages|adapters)/`;
  return [
    {
      name: "no-circular",
      severity: "error",
      from: from("^"),
      to: { circular: true, ...(excludeFixtures ? { pathNot: fixtureExclusion } : {}) },
    },
    {
      name: "not-to-unresolvable",
      severity: "error",
      from: from("^"),
      to: { couldNotResolve: true, ...(excludeFixtures ? { pathNot: fixtureExclusion } : {}) },
    },
    {
      name: "domain-not-to-outer-layers",
      severity: "error",
      from: from(domain),
      to: to(`${prefix}(?:packages/application|adapters|services|apps)/`),
    },
    {
      name: "domain-not-to-provider-or-runtime",
      severity: "error",
      from: from(domain),
      to: { dependencyTypes: ["core", "npm", "npm-dev", "npm-optional", "npm-peer"] },
    },
    {
      name: "application-not-to-outer-layers",
      severity: "error",
      from: from(application),
      to: to(`${prefix}(?:adapters|services|apps)/`),
    },
    {
      name: "entry-not-to-domain",
      severity: "error",
      from: from(entries),
      to: to(domain),
    },
    {
      name: "adapter-not-to-entry",
      severity: "error",
      from: from(adapters),
      to: to(entries),
    },
    {
      name: "production-not-to-test-support",
      severity: "error",
      from: from(production),
      to: to(`${prefix}test-support/`),
    },
  ];
}

const fixtureRules = layerRules(fixtureRoot, false);
const productionRules = layerRules(productionRoot, true).map((rule) => ({
  ...rule,
  name: `prod-${rule.name}`,
}));

export default {
  forbidden: [...fixtureRules, ...productionRules],
  options: {
    doNotFollow: {
      dependencyTypes: ["core", "npm", "npm-dev", "npm-optional", "npm-peer"],
    },
    tsConfig: { fileName: "tsconfig.base.json" },
    tsPreCompilationDeps: true,
  },
};
