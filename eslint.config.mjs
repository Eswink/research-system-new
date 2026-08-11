import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";

import architecture from "./tools/eslint-rules/architecture.mjs";

const nodeGlobals = {
  console: "readonly",
  process: "readonly",
};

export default defineConfig([
  {
    ignores: [
      "node_modules/**",
      ".pnpm-store/**",
      "dist/**",
      "build/**",
      "coverage/**",
      "tests/architecture/typescript/fixtures/invalid/**",
    ],
  },
  {
    files: ["**/*.mjs"],
    extends: [js.configs.recommended],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: nodeGlobals,
    },
  },
  {
    files: [
      "apps/**/*.{ts,tsx,mts,cts}",
      "services/**/*.{ts,tsx,mts,cts}",
      "packages/**/*.{ts,tsx,mts,cts}",
      "adapters/**/*.{ts,tsx,mts,cts}",
      "tests/architecture/typescript/fixtures/valid/**/*.ts",
      "tests/tooling/typescript/**/*.ts",
    ],
    extends: [tseslint.configs.strictTypeChecked, tseslint.configs.stylisticTypeChecked],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      architecture,
    },
    rules: {
      complexity: ["error", 15],
      "default-case": "error",
      "max-depth": ["error", 4],
      "max-len": [
        "error",
        {
          code: 100,
          ignoreComments: false,
          ignoreStrings: false,
          ignoreTemplateLiterals: false,
          ignoreUrls: true,
        },
      ],
      "max-lines": ["error", { max: 300, skipBlankLines: true, skipComments: true }],
      "max-lines-per-function": ["error", { max: 50, skipBlankLines: true, skipComments: true }],
      "max-nested-callbacks": ["error", 10],
      "max-params": ["error", 3],
      "no-restricted-syntax": [
        "error",
        {
          selector: "ImportExpression",
          message: "Dynamic imports require an explicit architecture exception.",
        },
        {
          selector: "TSImportType",
          message: "Inline import types are forbidden; use a top-level import type declaration.",
        },
        {
          selector: "Program > :not(ImportDeclaration) ~ ImportDeclaration",
          message: "All imports must appear before executable module statements.",
        },
      ],
      "@typescript-eslint/switch-exhaustiveness-check": "error",
      "architecture/require-never-default": "error",
    },
  },
]);
