import { useState } from "react";
import { TagInput } from "./reference/TagInput";

/** Drawer-owned tags reset with the draft form; never written to product state. */
export function ExampleTags({ initial = [], name }: { initial?: string[]; name: string }) {
  const [tags, setTags] = useState(initial);
  return <TagInput tags={tags} onChange={setTags} name={name} />;
}
