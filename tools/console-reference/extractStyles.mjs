/** Move constant presentational declarations to scoped CSS Modules, retaining dynamic inline values. */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const root = process.argv[2] ?? "apps/web/src/features/example-console/reference";
const unitless = new Set(
  `animationIterationCount aspectRatio borderImageOutset borderImageSlice borderImageWidth boxFlex boxFlexGroup boxOrdinalGroup columnCount columns fillOpacity flex flexGrow flexPositive flexShrink flexNegative flexOrder fontWeight gridArea gridColumn gridColumnEnd gridColumnSpan gridColumnStart gridRow gridRowEnd gridRowSpan gridRowStart lineClamp lineHeight opacity order orphans scale stopOpacity strokeDasharray strokeDashoffset strokeMiterlimit strokeOpacity strokeWidth tabSize widows zIndex zoom WebkitLineClamp`.split(
    " ",
  ),
);
const cssName = (key) =>
  key.startsWith("--")
    ? key
    : key.replace(/[A-Z]/g, (l) => "-" + l.toLowerCase()).replace(/^ms-/, "-ms-");
function valueOf(node, key) {
  if (ts.isStringLiteralLike(node)) return node.text;
  if (ts.isNumericLiteral(node))
    return node.text + (unitless.has(key) || node.text === "0" ? "" : "px");
  if (ts.isPrefixUnaryExpression(node) && ts.isNumericLiteral(node.operand)) {
    const sign = node.operator === ts.SyntaxKind.MinusToken ? "-" : "+";
    return sign + node.operand.text + (unitless.has(key) || node.operand.text === "0" ? "" : "px");
  }
  return undefined;
}
function nameOf(tag, items, existing) {
  const fields = Object.fromEntries(items);
  if (existing && /\bpanel\b/.test(existing)) return "panel";
  if (fields.display === "grid") return "grid";
  if (fields.display?.includes("flex")) return fields.flexDirection === "column" ? "column" : "row";
  if (tag === "button") return "action";
  if (tag === "input" || tag === "textarea" || tag === "select") return "field";
  if (fields.fontSize) return /^(8|9|10)px$/.test(fields.fontSize) ? "caption" : "label";
  if (fields.position === "absolute" || fields.position === "fixed") return "overlay";
  if (fields.height && fields.background) return "indicator";
  if (tag === "svg") return "chart";
  return "surface";
}
let moved = 0;
for (const filename of fs.readdirSync(root).filter((n) => n.endsWith(".tsx"))) {
  const file = path.join(root, filename);
  let s = fs.readFileSync(file, "utf8");
  if (s.includes("import visual from") || fs.existsSync(file.replace(/\.tsx$/, ".module.css")))
    continue;
  const sf = ts.createSourceFile(file, s, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const rules = [],
    edits = [],
    counts = {};
  function visit(node) {
    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      const attrs = node.attributes.properties;
      const style = attrs.find((a) => ts.isJsxAttribute(a) && a.name.text === "style");
      const styleNode = style?.initializer?.expression;
      if (
        styleNode &&
        ts.isObjectLiteralExpression(styleNode) &&
        !styleNode.properties.some(ts.isSpreadAssignment)
      ) {
        const constants = [],
          dynamic = [];
        for (const p of styleNode.properties) {
          if (!ts.isPropertyAssignment(p)) {
            dynamic.push(p.getText(sf));
            continue;
          }
          const key =
            ts.isIdentifier(p.name) || ts.isStringLiteral(p.name) ? p.name.text : undefined;
          const value = key ? valueOf(p.initializer, key) : undefined;
          if (value !== undefined) constants.push([key, value]);
          else dynamic.push(p.getText(sf));
        }
        if (constants.length) {
          const classAttr = attrs.find((a) => ts.isJsxAttribute(a) && a.name.text === "className");
          const existing = classAttr?.initializer;
          const base = nameOf(
            node.tagName.getText(sf),
            constants,
            existing && ts.isStringLiteral(existing) ? existing.text : undefined,
          );
          counts[base] = (counts[base] ?? 0) + 1;
          const cls = base + (counts[base] === 1 ? "" : counts[base]);
          rules.push(
            `:global([data-design-surface]) .${cls} {\n${constants.map(([k, v]) => "  " + cssName(k) + ": " + v + ";").join("\n")}\n}`,
          );
          const classText =
            existing && ts.isStringLiteral(existing)
              ? `className={\`${existing.text} \${visual.${cls}}\`}`
              : existing && ts.isJsxExpression(existing) && existing.expression
                ? `className={[${existing.expression.getText(sf)}, visual.${cls}].filter(Boolean).join(" ")}`
                : `className={visual.${cls}}`;
          if (classAttr)
            edits.push({ start: classAttr.getStart(sf), end: classAttr.end, text: classText });
          const remaining = dynamic.length ? `style={{ ${dynamic.join(", ")} }}` : "";
          edits.push({
            start: style.getStart(sf),
            end: style.end,
            text: (classAttr ? "" : classText + " ") + remaining,
          });
          moved += constants.length;
        }
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(sf);
  if (!rules.length) continue;
  edits.sort((a, b) => b.start - a.start);
  for (const e of edits) s = s.slice(0, e.start) + e.text + s.slice(e.end);
  const stem = filename.slice(0, -4);
  s = `import visual from "./${stem}.module.css";\n` + s;
  fs.writeFileSync(file, s, "utf8");
  fs.writeFileSync(
    path.join(root, stem + ".module.css"),
    `/* Scoped styles migrated from the supplied design; dynamic state remains in TSX. */\n` +
      rules.join("\n\n") +
      "\n",
    "utf8",
  );
}
console.log("Migrated", moved, "constant declarations without altering state-dependent styles");
