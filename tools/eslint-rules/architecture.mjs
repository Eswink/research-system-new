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

export default {
  rules: {
    "require-never-default": requireNeverDefault,
  },
};
