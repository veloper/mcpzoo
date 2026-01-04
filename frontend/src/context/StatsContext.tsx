// StatsContext removed — historically provided polling for per-pid stats.
// This module is now deprecated. Do not import it; rely on `useSystemSnapshots` for inline stats.

export function StatsProvider(): any {
  throw new Error('StatsProvider has been removed. Use `useSystemSnapshots` and remove imports of StatsContext.')
}

export function useStatsHistory(): any {
  throw new Error('useStatsHistory has been removed. Use `useSystemSnapshots` instead to read inline stats fields.')
}