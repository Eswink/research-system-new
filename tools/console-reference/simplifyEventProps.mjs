import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(path.resolve("apps/web/package.json"));
const ts = require("typescript");
const root = "apps/web/src/features/example-console/reference";
const files = [
  "event-drawer/EventDrawerEvActor.tsx",
  "event-drawer/EventDrawerEvActor2.tsx",
  "timeline-screen/TimelineSection2.tsx",
  "timeline-screen/TimelineSection3.tsx",
  "timeline-screen/TimelineSection8.tsx",
];
const replacements = new Map([
  ["ev", "E.Event"],
  ["filteredEvents", "E.Event[]"],
  ["selectedEvent", "E.Event | null"],
  ["setSelectedEvent", "Dispatch<SetStateAction<E.Event | null>>"],
  ["agent", "E.Agent | null | undefined"],
  ["model", "E.Model | null | undefined"],
]);

for (const name of files) {
  const file = path.join(root, name);
  let source = fs.readFileSync(file, "utf8");
  const parsed = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const edits = [];
  for (const declaration of parsed.statements.filter(ts.isInterfaceDeclaration)) {
    for (const member of declaration.members) {
      const alias = replacements.get(member.name?.getText(parsed));
      if (alias && member.type) {
        edits.push({ start: member.type.getStart(parsed), end: member.type.end, text: alias });
      }
    }
  }
  for (const edit of edits.sort((a, b) => b.start - a.start)) {
    source = source.slice(0, edit.start) + edit.text + source.slice(edit.end);
  }
  if (!source.includes('import type * as E from "../../exampleTypes"')) {
    source = 'import type * as E from "../../exampleTypes";\n' + source;
  }
  fs.writeFileSync(file, source, "utf8");
  console.log(name, "reused", edits.length, "fixture-derived event/actor contracts");
}
