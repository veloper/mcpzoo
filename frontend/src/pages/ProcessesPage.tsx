import React, { useState, useEffect, useMemo } from 'react'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"
import {
  Activity,
  Square,
  Play,
  Pause,
  X,
  ChevronUp,
  ChevronDown,
  Loader2,
} from "lucide-react"
import { useProcesses, Process } from '../hooks/useProcesses'
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

interface ProcessTreeTableProps {
  processes: Process[]
}

function ProcessTreeTable({ processes }: ProcessTreeTableProps) {
  // Build tree structure from processes
  const buildTree = (procs: Process[]): Process[] => {
    const procMap = new Map<number, Process>()
    const roots: Process[] = []

    // Create a copy of processes with children arrays
    procs.forEach(proc => {
      procMap.set(proc.pid, { ...proc, children: [] })
    })

    // Build parent-child relationships
    procMap.forEach(proc => {
      if (proc.ppid && proc.ppid !== proc.pid) { // Avoid self-references
        const parent = procMap.get(proc.ppid)
        if (parent && parent.children) {
          parent.children.push(proc)
        } else {
          roots.push(proc)
        }
      } else {
        roots.push(proc)
      }
    })

    return roots
  }

  const renderTreeNode = (process: Process, prefix = '', isLast = true, depth = 0): React.ReactNode[] => {
    const nodes: React.ReactNode[] = []

    // Create the tree prefix with box characters
    const treePrefix = prefix + (isLast ? '└── ' : '├── ')
    const childPrefix = prefix + (isLast ? '      ' : '│     ')

    // Display name: use command if available, otherwise name
    const displayName = process.command || process.name || 'unknown'

    // Calculate flex based on depth: level 0 = 0.25, level 2 = 0.50, level 3 = 0.75
    const prefixFlex = depth === 0 ? 0.002 : 0.002 * depth

    nodes.push(
      <TableRow key={process.pid}>
        <TableCell className="font-mono text-sm">
          <div className="flex">
            <span
              className="text-muted-foreground whitespace-pre"
              style={{ flexGrow: prefixFlex, flexShrink: 0 }}
            >
              {treePrefix}
            </span>
            <span className="flex-1">
              {displayName}
            </span>
          </div>
        </TableCell>
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
        <TableCell className="text-right font-mono text-sm">
          {process.cpu_percent !== undefined ? `${process.cpu_percent.toFixed(1)}\u00A0%` : '--'}
        </TableCell>
        <TableCell className="text-right font-mono text-sm">
          {process.memory_percent !== undefined ? `${process.memory_percent.toFixed(1)}\u00A0%` : '--'}
        </TableCell>
        <TableCell className="text-right font-mono text-sm">
          {process.pid}
        </TableCell>
      </TableRow>
    )

    // Render children
    if (process.children && process.children.length > 0) {
      process.children.forEach((child, index) => {
        const isLastChild = index === process.children!.length - 1
        nodes.push(...renderTreeNode(child, childPrefix, isLastChild, depth + 1))
      })
    }

    return nodes
  }

  const treeRoots = buildTree(processes)

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="font-semibold text-foreground">Process/Command Tree</TableHead>
            <TableHead className="font-semibold text-foreground">State</TableHead>
            <TableHead className="font-semibold text-foreground text-right w-24 min-w-24 whitespace-nowrap">CPU %</TableHead>
            <TableHead className="font-semibold text-foreground text-right w-24 min-w-24 whitespace-nowrap">Memory %</TableHead>
            <TableHead className="font-semibold text-foreground text-right">PID</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {treeRoots.map((root, index) => {
            const isLastRoot = index === treeRoots.length - 1
            return renderTreeNode(root, '', isLastRoot)
          })}
        </TableBody>
      </Table>
    </div>
  )
}

type SortDirection = 'asc' | 'desc' | null

export default function ProcessesPage() {
  const { processes, loading, error, refetch, refresh } = useProcesses()
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [autoReloadPercent, setAutoReloadPercent] = useState(0)
  const [autoReloadInterval, setAutoReloadInterval] = useState(5000) // 5 seconds
  const [updateInterval, setUpdateInterval] = useState(100) // 100ms updates
  const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null)
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)

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

  // Sorting logic
  const handleSort = (column: string) => {
    if (sortColumn === column) {
      // Cycle through: asc -> desc -> null
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortDirection(null)
        setSortColumn(null)
      }
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  const sortedProcesses = useMemo(() => {
    if (!sortColumn || !sortDirection) return processes

    return [...processes].sort((a, b) => {
      let aValue: any = a[sortColumn as keyof Process]
      let bValue: any = b[sortColumn as keyof Process]

      // Handle undefined/null values
      if (aValue == null && bValue == null) return 0
      if (aValue == null) return sortDirection === 'asc' ? 1 : -1
      if (bValue == null) return sortDirection === 'asc' ? -1 : 1

      // Handle numeric values
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
      }

      // Handle string values
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const comparison = aValue.localeCompare(bValue)
        return sortDirection === 'asc' ? comparison : -comparison
      }

      // Convert to strings for comparison
      const aStr = String(aValue)
      const bStr = String(bValue)
      const comparison = aStr.localeCompare(bStr)
      return sortDirection === 'asc' ? comparison : -comparison
    })
  }, [processes, sortColumn, sortDirection])

  const getSortIcon = (column: string) => {
    if (sortColumn !== column) return null
    return sortDirection === 'asc' ?
      <ChevronUp className="h-4 w-4 ml-1" /> :
      <ChevronDown className="h-4 w-4 ml-1" />
  }

  const totalProcesses = processes.length
  const runningProcesses = processes.filter(p => p.state === 'RUNNING').length

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
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

      <Tabs defaultValue="list" className="w-full">
        <TabsList>
          <TabsTrigger value="list">List</TabsTrigger>
          <TabsTrigger value="tree">Tree</TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="space-y-4">
          <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12" />
                  <TableHead
                    className="font-semibold text-foreground cursor-pointer hover:bg-muted/50 select-none"
                    onClick={() => handleSort('pid')}
                  >
                    <div className="flex items-center">
                      PID
                      {getSortIcon('pid')}
                    </div>
                  </TableHead>
                  <TableHead
                    className="font-semibold text-foreground cursor-pointer hover:bg-muted/50 select-none"
                    onClick={() => handleSort('ppid')}
                  >
                    <div className="flex items-center">
                      PPID
                      {getSortIcon('ppid')}
                    </div>
                  </TableHead>
                  <TableHead
                    className="font-semibold text-foreground cursor-pointer hover:bg-muted/50 select-none"
                    onClick={() => handleSort('name')}
                  >
                    <div className="flex items-center">
                      Name
                      {getSortIcon('name')}
                    </div>
                  </TableHead>
                  <TableHead
                    className="font-semibold text-foreground text-right w-24 min-w-24 whitespace-nowrap cursor-pointer hover:bg-muted/50 select-none"
                    onClick={() => handleSort('cpu_percent')}
                  >
                    <div className="flex items-center justify-end">
                      CPU %
                      {getSortIcon('cpu_percent')}
                    </div>
                  </TableHead>
                  <TableHead
                    className="font-semibold text-foreground text-right w-24 min-w-24 whitespace-nowrap cursor-pointer hover:bg-muted/50 select-none"
                    onClick={() => handleSort('memory_percent')}
                  >
                    <div className="flex items-center justify-end">
                      Memory %
                      {getSortIcon('memory_percent')}
                    </div>
                  </TableHead>
                  <TableHead
                    className="font-semibold text-foreground text-right cursor-pointer hover:bg-muted/50 select-none"
                    onClick={() => handleSort('memory_rss')}
                  >
                    <div className="flex items-center justify-end">
                      Memory
                      {getSortIcon('memory_rss')}
                    </div>
                  </TableHead>
                  <TableHead
                    className="font-semibold text-foreground cursor-pointer hover:bg-muted/50 select-none"
                    onClick={() => handleSort('command')}
                  >
                    <div className="flex items-center">
                      Command
                      {getSortIcon('command')}
                    </div>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedProcesses.map((process) => (
                  <TableRow key={process.pid}>
                    <TableCell className="w-8">
                      {getProcessIcon(process.state)}
                    </TableCell>
                    <TableCell className="font-mono text-sm">{process.pid}</TableCell>
                    <TableCell className="font-mono text-sm">{process.ppid || '--'}</TableCell>
                    <TableCell className="font-medium">{process.name}</TableCell>
                    <TableCell className="text-right font-mono text-sm">
                      {process.cpu_percent !== undefined ? `${process.cpu_percent.toFixed(1)}%` : '--'}
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">
                      {process.memory_percent !== undefined ? `${process.memory_percent.toFixed(1)}%` : '--'}
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm whitespace-nowrap">
                      {process.memory_rss ? formatBytes(process.memory_rss) : '--'}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
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
        </TabsContent>

        <TabsContent value="tree" className="space-y-4">
          <ProcessTreeTable processes={processes} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
