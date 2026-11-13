/** Present API difficulty values as readable labels without changing their values. */
export function formatDifficulty(difficulty: string): string {
  return difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
}
