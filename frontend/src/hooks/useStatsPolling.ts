// useStatsPolling removed — Stats are now handled inline by `useProcesses`.
export function useStatsPolling(): any {
  throw new Error('useStatsPolling has been removed. Use `useProcesses` instead.')
}