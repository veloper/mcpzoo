import React, { useState, useEffect } from 'react'
import { Switch } from "@/components/ui/switch"
import { CircularProgress } from "@/components/ui/circular-progress"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import {
  Activity,
  Square,
  Play,
  Pause,
  X,
} from "lucide-react"
import { useProcesses } from '../hooks/useProcesses'
import { formatBytes } from '../utils/format'

function getProcessIcon(state: string) {
  switch (state.toLowerCase()) {
    case 'running':
      return <Play className="h-4 w-4 text-green-500" />
    case 'stopped':
    case 'exited':
      return <Square className="h-4 w-4 text-red-500" />
    case 'sleeping':
    case 'waiting':
      return <Pause className="h-4 w-4 text-yellow-500" />
    case 'zombie':
      return <X className="h-4 w-4 text-gray-500" />
    default:
      return <Activity className="h-4 w-4 text-muted-foreground" />
  }
}

export default function ProcessesPage() {
  const { processes, loading, error, refetch, refresh } = useProcesses()
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [autoReloadPercent, setAutoReloadPercent] = useState(0)
  const [autoReloadInterval, setAutoReloadInterval] = useState(5000) // 5 seconds
  const [updateInterval, setUpdateInterval] = useState(100) // 100ms updates
  const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null)

  // Calculate increment per update based on intervals
  const incrementPerUpdate = 100 / (autoReloadInterval / updateInterval)

  // Effect 1: Independent Timer (manages percentage state)
  useEffect(() => {
    if (!autoRefresh) {
      setAutoReloadPercent(0)
      return
    }

    const increment = () => {
      setAutoReloadPercent(prev => {
        const next = prev + incrementPerUpdate
        return next >= 100 ? 0 : next // Reset at 100%
      })
    }

    const interval = setInterval(increment, updateInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, incrementPerUpdate, updateInterval])

  // Effect 2: Refresh Trigger (reacts to percentage resets)
  useEffect(() => {
    if (autoReloadPercent === 0 && autoRefresh) {
      refresh()
        .then(() => {
          setLastRefreshTime(new Date())
          console.log('✅ Process tree refreshed successfully')
        })
        .catch((error) => {
          console.error('❌ Failed to refresh process tree:', error)
        }) // Trigger refresh when percent resets to 0
    }
  }, [autoReloadPercent, autoRefresh, refresh])

  // Effect 3: UI Progression (reacts to percentage for UI updates)
  useEffect(() => {
    // CircularProgress automatically updates via state binding
    // Could add other UI side effects here if needed
  }, [autoReloadPercent])

  const totalProcesses = processes.length
  const runningProcesses = processes.filter(p => p.state === 'RUNNING').length

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading process tree...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <X className="h-8 w-8 mx-auto mb-4 text-red-500" />
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={refetch} className="px-4 py-2 bg-primary text-primary-foreground rounded">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Processes</h1>
          <p className="text-muted-foreground">
            {totalProcesses} processes total, {runningProcesses} running
            {lastRefreshTime && (
              <span className="ml-4 text-xs">
                Last refresh: {lastRefreshTime.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">Auto-refresh</span>
          <Switch
            checked={autoRefresh}
            onCheckedChange={setAutoRefresh}
          />
          {autoRefresh && (
            <CircularProgress
              progress={autoReloadPercent}
              size={20}
              strokeWidth={2}
              className="text-primary"
            />
          )}
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12" />
              <TableHead className="font-semibold text-foreground">PID</TableHead>
              <TableHead className="font-semibold text-foreground">Name</TableHead>
              <TableHead className="font-semibold text-foreground">State</TableHead>
              <TableHead className="font-semibold text-foreground">User</TableHead>
              <TableHead className="font-semibold text-foreground text-right">CPU %</TableHead>
              <TableHead className="font-semibold text-foreground text-right">Memory %</TableHead>
              <TableHead className="font-semibold text-foreground text-right">Memory</TableHead>
              <TableHead className="font-semibold text-foreground">Command</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {processes.map((process) => (
              <TableRow key={process.pid}>
                <TableCell className="w-8">
                  {getProcessIcon(process.state)}
                </TableCell>
                <TableCell className="font-mono text-sm">{process.pid}</TableCell>
                <TableCell className="font-medium">{process.name}</TableCell>
                <TableCell>
                  <span className={cn(
                    "px-2 py-1 rounded-full text-xs font-medium",
                    process.state === 'RUNNING' && "bg-green-100 text-green-800",
                    process.state === 'STOPPED' && "bg-red-100 text-red-800",
                    process.state === 'SLEEPING' && "bg-yellow-100 text-yellow-800",
                    process.state === 'EXITED' && "bg-gray-100 text-gray-800"
                  )}>
                    {process.state}
                  </span>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {process.user || '--'}
                </TableCell>
                <TableCell className="text-right font-mono text-sm">
                  {process.cpu_percent !== undefined ? `${process.cpu_percent.toFixed(1)}%` : '--'}
                </TableCell>
                <TableCell className="text-right font-mono text-sm">
                  {process.memory_percent !== undefined ? `${process.memory_percent.toFixed(1)}%` : '--'}
                </TableCell>
                <TableCell className="text-right font-mono text-sm">
                  {process.memory_rss ? formatBytes(process.memory_rss) : '--'}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground max-w-xs truncate">
                  {process.command || '--'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center gap-6 text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <Play className="h-3.5 w-3.5 text-green-500" />
          <span>Running processes</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Square className="h-3.5 w-3.5 text-red-500" />
          <span>Stopped/exited processes</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Pause className="h-3.5 w-3.5 text-yellow-500" />
          <span>Sleeping processes</span>
        </div>
      </div>
    </div>
  )
}
