/** Fail closed on corrupt bundled design data instead of asserting away missing values. */
export function requiredExample<T>(value: T | null | undefined): T {
  if (value === null || value === undefined) {
    throw new Error("Incomplete bundled example; no live request was made");
  }
  return value;
}
