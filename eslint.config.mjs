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
      "apps/web/dist/**",
      "apps/web/node_modules/**",
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
      ".cursor/skills/parallel-agent-orchestration/scripts/**/*.ts",
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
      "architecture/max-lines-soft": [
        "warn",
        { softMax: 300, hardMax: 450, skipBlankLines: true, skipComments: true },
      ],
      "architecture/max-lines-hard": [
        "error",
        { softMax: 300, hardMax: 450, skipBlankLines: true, skipComments: true },
      ],
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
  {
    files: ["apps/web/**/*.{ts,tsx}"],
    languageOptions: {
      parserOptions: {
        projectService: false,
        project: ["./apps/web/tsconfig.json"],
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    files: ["apps/web/tests/**/*.ts"],
    rules: {
      "@typescript-eslint/no-floating-promises": "off",
      "@typescript-eslint/no-unsafe-assignment": "off",
      "@typescript-eslint/no-unsafe-member-access": "off",
      "@typescript-eslint/no-unsafe-argument": "off",
      "@typescript-eslint/no-base-to-string": "off",
      "@typescript-eslint/no-unnecessary-type-assertion": "off",
      "@typescript-eslint/require-await": "off",
      "@typescript-eslint/consistent-type-definitions": "off",
    },
  },
  {
    // node:test 回调返回 promise 由 runner 消费；与 apps/web/tests 同一先例。
    files: ["tests/tooling/typescript/**/*.ts", ".cursor/skills/**/scripts/*.test.ts"],
    rules: {
      "@typescript-eslint/no-floating-promises": "off",
    },
  },
  {
    // API DTO 契约文件（apps/web/src/api/types.ts）：与 schemas/openapi.m13.json
    // 对应的单一 schema truth（生成边界）；声明式类型允许超出行数阈值。
    files: ["apps/web/src/api/types.ts"],
    rules: {
      "architecture/max-lines-soft": "off",
      "architecture/max-lines-hard": "off",
    },
  },
]);
