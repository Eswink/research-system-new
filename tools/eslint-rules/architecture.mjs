const isAssertNeverCall = (expression) =>
  expression?.type === "CallExpression" &&
  expression.callee.type === "Identifier" &&
  expression.callee.name === "assertNever";

const isNeverAssignment = (statement) =>
  statement.type === "VariableDeclaration" &&
  statement.declarations.some(
    (declaration) =>
      declaration.id.type === "Identifier" &&
      declaration.id.typeAnnotation?.typeAnnotation.type === "TSNeverKeyword" &&
      declaration.init !== null,
  );

const executesNeverCheck = (statement) => {
  if (isNeverAssignment(statement)) {
    return true;
  }
  if (statement.type === "BlockStatement") {
    return statement.body.some(executesNeverCheck);
  }
  if (statement.type === "ExpressionStatement") {
    return isAssertNeverCall(statement.expression);
  }
  if (statement.type === "ReturnStatement" || statement.type === "ThrowStatement") {
    return isAssertNeverCall(statement.argument);
  }
  return false;
};

const requireNeverDefault = {
  meta: {
    type: "problem",
    docs: {
      description: "Require switch default branches to execute a never exhaustiveness check",
    },
    schema: [],
    messages: {
      missingNeverCheck: "The default branch must execute assertNever(...) or assign to never.",
    },
  },
  create(context) {
    return {
      "SwitchCase[test=null]"(node) {
        if (!node.consequent.some(executesNeverCheck)) {
          context.report({ node, messageId: "missingNeverCheck" });
        }
      },
    };
  },
};

const commentOnlyLineNumbers = (sourceCode) => {
  const lines = new Set();
  for (const comment of sourceCode.getAllComments()) {
    const before = sourceCode.getTokenBefore(comment, { includeComments: true });
    const after = sourceCode.getTokenAfter(comment, { includeComments: true });
    const start =
      before !== null && before.loc.end.line === comment.loc.start.line
        ? comment.loc.start.line + 1
        : comment.loc.start.line;
    const end =
      after !== null && after.loc.start.line === comment.loc.end.line
        ? comment.loc.end.line - 1
        : comment.loc.end.line;
    for (let line = start; line <= end; line += 1) {
      lines.add(line);
    }
  }
  return lines;
};

const countLines = (sourceCode, skipBlankLines, skipComments) => {
  const rawLines = sourceCode.lines;
  const lines =
    rawLines.length > 1 && rawLines[rawLines.length - 1] === "" ? rawLines.slice(0, -1) : rawLines;
  const commentLines = skipComments ? commentOnlyLineNumbers(sourceCode) : new Set();
  return lines.filter((text, index) => {
    if (skipBlankLines && text.trim() === "") {
      return false;
    }
    return !commentLines.has(index + 1);
  }).length;
};

const lineLimitSchema = [
  {
    type: "object",
    properties: {
      softMax: { type: "integer", minimum: 0 },
      hardMax: { type: "integer", minimum: 1 },
      skipBlankLines: { type: "boolean" },
      skipComments: { type: "boolean" },
    },
    additionalProperties: false,
  },
];

const readLineLimitOptions = (context) => {
  const {
    softMax = 300,
    hardMax = 450,
    skipBlankLines = false,
    skipComments = false,
  } = context.options[0] ?? {};
  const sourceCode = context.sourceCode ?? context.getSourceCode();
  return { softMax, hardMax, actual: countLines(sourceCode, skipBlankLines, skipComments) };
};

// 软阈值规则：配置为 "warn"，仅在 (softMax, hardMax] 区间报告，提示评估拆分。
const maxLinesSoft = {
  meta: {
    type: "suggestion",
    docs: {
      description: "Warn when a file exceeds the soft line limit but not the hard limit",
    },
    schema: lineLimitSchema,
    messages: {
      exceedSoft: "File has {{actual}} lines (soft limit {{softMax}}); consider splitting.",
    },
  },
  create(context) {
    return {
      "Program:exit"(node) {
        const { softMax, hardMax, actual } = readLineLimitOptions(context);
        if (actual > softMax && actual <= hardMax) {
          context.report({ node, messageId: "exceedSoft", data: { actual, softMax } });
        }
      },
    };
  },
};

// 硬上限规则：配置为 "error"，仅在超过 hardMax 时报告，必须拆分。
const maxLinesHard = {
  meta: {
    type: "suggestion",
    docs: {
      description: "Error when a file exceeds the hard line limit",
    },
    schema: lineLimitSchema,
    messages: {
      exceedHard:
        "File has {{actual}} lines, exceeding hard limit {{hardMax}}; splitting is required.",
    },
  },
  create(context) {
    return {
      "Program:exit"(node) {
        const { hardMax, actual } = readLineLimitOptions(context);
        if (actual > hardMax) {
          context.report({ node, messageId: "exceedHard", data: { actual, hardMax } });
        }
      },
    };
  },
};

export default {
  rules: {
    "require-never-default": requireNeverDefault,
    "max-lines-soft": maxLinesSoft,
    "max-lines-hard": maxLinesHard,
  },
};
