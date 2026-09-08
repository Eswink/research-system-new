/** 连接 class 名（CSS module 属性可能为 undefined；过滤空值） */
export function cx(...parts: (string | false | null | undefined)[]): string {
  const picked: string[] = [];
  for (const part of parts) {
    if (typeof part === "string" && part.length > 0) {
      picked.push(part);
    }
  }
  return picked.join(" ");
}
