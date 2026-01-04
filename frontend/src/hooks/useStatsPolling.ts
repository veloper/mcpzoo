// useStatsPolling removed — Stats are now handled inline by `useSystemSnapshots`.
export function useStatsPolling(): any {
  throw new Error('useStatsPolling has been removed. Use `useSystemSnapshots` instead.')
}