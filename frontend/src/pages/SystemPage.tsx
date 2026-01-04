import React, { useState, useEffect, useMemo } from 'react'
import { useSystemSnapshots, SystemSnapshotProcess } from '../hooks/useSystemSnapshots'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { CircularProgress } from '@/components/ui/circular-progress'
import { Sparkline } from '@/components/ui/sparkline'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import { Activity, Square, Play, Moon, X, ChevronUp, ChevronDown, Loader2 } from "lucide-react"
import { formatBytes } from '../utils/format'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Legend, Brush, ResponsiveContainer } from 'recharts'

type ProcessTreeNode = SystemSnapshotProcess & {
  children: ProcessTreeNode[]
}

// Helper: Get icon based on process state
function getProcessIcon(state: string) {
  switch (state.toLowerCase()) {
    case 'running':
      return <Play className="h-4 w-4 text-green-500" />
    case 'stopped':
    case 'exited':
      return <Square className="h-4 w-4 text-red-500" />
    case 'sleeping':
    case 'waiting':
      return <Moon className="h-4 w-4 text-yellow-500" />
    case 'zombie':
      return <X className="h-4 w-4 text-gray-500" />
    default:
      return <Activity className="h-4 w-4 text-muted-foreground" />
  }
}

// ProcessTreeTable Component: Displays processes in tree structure
interface ProcessTreeTableProps {
  processes: SystemSnapshotProcess[]
  getProcessHistory: (pid: number) => Array<{ timestamp: string; cpu_percent: number | null; memory_percent: number | null; memory_rss: number | null }>
  onChartClick: (process: SystemSnapshotProcess, type: 'cpu' | 'memory') => void
}

function ProcessTreeTable({ processes, getProcessHistory, onChartClick }: ProcessTreeTableProps) {
  const buildTree = (procs: SystemSnapshotProcess[]): ProcessTreeNode[] => {
    const procMap = new Map<number, ProcessTreeNode>()
    const roots: ProcessTreeNode[] = []

    procs.forEach(proc => {
      procMap.set(proc.pid, { ...proc, children: [] })
    })

    procMap.forEach(proc => {
      if (proc.ppid && proc.ppid !== proc.pid) {
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

  const renderTreeNode = (process: SystemSnapshotProcess & { children?: SystemSnapshotProcess[] }, prefix = '', isLast = true, depth = 0): React.ReactNode[] => {
    const nodes: React.ReactNode[] = []
    const treePrefix = prefix + (isLast ? '└── ' : '├── ')
    const childPrefix = prefix + (isLast ? '      ' : '│     ')
    const displayName = process.command || process.name || 'unknown'
    const fullCommand = process.arguments ? `${displayName} ${process.arguments}` : displayName
    const prefixFlex = depth === 0 ? 0.002 : 0.002 * depth
    
    const history = getProcessHistory(process.pid)
    const cpuData = history.map(h => h.cpu_percent ?? 0).reverse()
    const memoryData = history.map(h => h.memory_percent ?? 0).reverse()

    nodes.push(
      <TableRow key={process.pid}>
        <TableCell className="font-mono text-sm">
          <div className="flex">
            <span className="text-muted-foreground whitespace-pre" style={{ flexGrow: prefixFlex, flexShrink: 0 }}>
              {treePrefix}
            </span>
            <span className="flex-1">{fullCommand}</span>
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
        <TableCell className="text-right">
          <div className="flex items-center justify-end gap-2">
            <span className="font-mono text-sm">
              {process.cpu_percent !== undefined && process.cpu_percent !== null ? `${process.cpu_percent.toFixed(1)}\u00A0%` : '--'}
            </span>
            {cpuData.length > 1 && (
              <button
                onClick={() => onChartClick(process, 'cpu')}
                className="cursor-pointer hover:opacity-75 transition-opacity"
              >
                <Sparkline data={cpuData} width={40} height={16} className="text-green-500" />
              </button>
            )}
          </div>
        </TableCell>
        <TableCell className="text-right">
          <div className="flex items-center justify-end gap-2">
            <span className="font-mono text-sm">
              {process.memory_percent !== undefined && process.memory_percent !== null ? `${process.memory_percent.toFixed(1)}\u00A0%` : '--'}
            </span>
            {memoryData.length > 1 && (
              <button
                onClick={() => onChartClick(process, 'memory')}
                className="cursor-pointer hover:opacity-75 transition-opacity"
              >
                <Sparkline data={memoryData} width={40} height={16} className="text-blue-500" />
              </button>
            )}
          </div>
        </TableCell>
        <TableCell className="text-right font-mono text-sm">
          {process.pid}
        </TableCell>
      </TableRow>
    )

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

// Main SystemPage Component
export default function SystemPage() {
  const { latestSnapshot, processes, refresh, loading, snapshots, getProcessHistory } = useSystemSnapshots()
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [autoReloadPercent, setAutoReloadPercent] = useState(0)
  const [autoReloadInterval, setAutoReloadInterval] = useState(5000) // 5 seconds hardcoded
  const [updateInterval, setUpdateInterval] = useState(100) // 100ms UI updates
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)
  
  // Chart dialog state
  const [chartDialogOpen, setChartDialogOpen] = useState(false)
  const [selectedProcess, setSelectedProcess] = useState<SystemSnapshotProcess | null>(null)
  const [chartType, setChartType] = useState<'cpu' | 'memory'>('cpu')
  const [systemChartOpen, setSystemChartOpen] = useState(false)
  const [systemChartType, setSystemChartType] = useState<'cpu' | 'memory'>('cpu')
  
  // Zoom state for charts
  const [processChartZoom, setProcessChartZoom] = useState({ start: 0, end: 100 })
  const [systemChartZoom, setSystemChartZoom] = useState({ start: 0, end: 100 })

  // Reset zoom when dialog opens
  useEffect(() => {
    if (chartDialogOpen) {
      setProcessChartZoom({ start: 0, end: 100 })
    }
  }, [chartDialogOpen])

  useEffect(() => {
    if (systemChartOpen) {
      setSystemChartZoom({ start: 0, end: 100 })
    }
  }, [systemChartOpen])

  const incrementPerUpdate = 100 / (autoReloadInterval / updateInterval)

  // Auto-refresh percentage counter effect
  useEffect(() => {
    if (!autoRefresh) {
      setAutoReloadPercent(0)
      return
    }

    const increment = () => {
      setAutoReloadPercent(prev => {
        const next = prev + incrementPerUpdate
        return next >= 100 ? 0 : next
      })
    }

    const interval = setInterval(increment, updateInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, incrementPerUpdate, updateInterval])

  // Auto-refresh trigger effect
  useEffect(() => {
    if (autoReloadPercent === 0 && autoRefresh) {
      refresh().catch(() => {
        // Silent failure - error already handled in hook
      })
    }
  }, [autoReloadPercent, autoRefresh, refresh])

  // Format timestamp to local timezone (display only)
  const formatLocalTime = (isoString: string): string => {
    const date = new Date(isoString)
    return date.toLocaleString()
  }

  // Get system-level historical data
  const getSystemHistory = () => {
    const sorted = [...snapshots].sort((a, b) => {
      return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    })
    return sorted.map(snapshot => ({
      cpu_percent: snapshot.cpu_percent,
      memory_percent: snapshot.memory_percent,
      timestamp: snapshot.timestamp
    }))
  }

  // Prepare chart data for dialog - memoized by pid
  const chartDataCache = useMemo(() => {
    const cache = new Map<number, any[]>()
    return (pid: number) => {
      if (!cache.has(pid)) {
        const history = getProcessHistory(pid)
        cache.set(pid, history
          .reverse()
          .map((item) => {
            const timeStr = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
            return {
              timeLabel: timeStr,
              cpu: item.cpu_percent ?? null,
              memory: item.memory_percent ?? null,
            }
          })
        )
      }
      return cache.get(pid)!
    }
  }, [snapshots])

  // Prepare system-level chart data - memoized, limited to recent items
  const systemChartData = useMemo(() => {
    const limit = 100 // Only show last 100 snapshots
    const recentSnapshots = snapshots.slice(0, limit)
    return recentSnapshots
      .reverse()
      .map((snapshot) => {
        const timeStr = new Date(snapshot.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        return {
          timeLabel: timeStr,
          cpu: snapshot.cpu_percent,
          memory: snapshot.memory_percent,
        }
      })
  }, [snapshots])

  // Sorting logic
  const handleSort = (column: string) => {
    if (sortColumn === column) {
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
      let aValue: any = a[sortColumn as keyof SystemSnapshotProcess]
      let bValue: any = b[sortColumn as keyof SystemSnapshotProcess]

      if (aValue == null && bValue == null) return 0
      if (aValue == null) return sortDirection === 'asc' ? 1 : -1
      if (bValue == null) return sortDirection === 'asc' ? -1 : 1

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const comparison = aValue.localeCompare(bValue)
        return sortDirection === 'asc' ? comparison : -comparison
      }

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

  if (loading && !latestSnapshot) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading system data...</p>
        </div>
      </div>
    )
  }

  const stats = latestSnapshot ? {
    cpu: latestSnapshot.cpu_percent,
    memory: latestSnapshot.memory_percent,
    load: latestSnapshot.load_average,
    timestamp: formatLocalTime(latestSnapshot.timestamp)
  } : null

  const totalProcesses = processes.length
  const runningProcesses = processes.filter(p => p.state === 'RUNNING').length

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-3xl font-bold">System</h1>
      </div>

      {/* TOP ROW: System Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">CPU Usage</div>
          <div className="flex items-end justify-between gap-4">
            <div className="text-2xl font-bold">{stats?.cpu.toFixed(1) || '--'}%</div>
            {getSystemHistory().length > 1 && (
              <button
                onClick={() => {
                  setSystemChartType('cpu')
                  setSystemChartOpen(true)
                }}
                className="cursor-pointer hover:opacity-75 transition-opacity"
              >
                <Sparkline 
                  data={getSystemHistory().map(s => s.cpu_percent)} 
                  width={200} 
                  height={24} 
                  className="text-green-500"
                />
              </button>
            )}
          </div>
        </div>
        
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Memory Usage</div>
          <div className="flex items-end justify-between gap-4">
            <div className="text-2xl font-bold">{stats?.memory.toFixed(1) || '--'}%</div>
            {getSystemHistory().length > 1 && (
              <button
                onClick={() => {
                  setSystemChartType('memory')
                  setSystemChartOpen(true)
                }}
                className="cursor-pointer hover:opacity-75 transition-opacity"
              >
                <Sparkline 
                  data={getSystemHistory().map(s => s.memory_percent)} 
                  width={200} 
                  height={24} 
                  className="text-blue-500"
                />
              </button>
            )}
          </div>
        </div>
        
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Load Average</div>
          <div className="text-sm font-mono">
            {stats?.load ? stats.load.map(l => l.toFixed(2)).join(', ') : '--'}
          </div>
        </div>

        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Last Update</div>
          <div className="text-sm font-mono">{stats?.timestamp || '--'}</div>
        </div>
      </div>

      {/* Auto-Refresh Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Processes</h2>
          <p className="text-sm text-muted-foreground">
            {totalProcesses} processes total, {runningProcesses} running
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

      {/* BOTTOM ROW: Process Tabs - List and Tree views */}
      <Tabs defaultValue="list" className="w-full">
        <TabsList>
          <TabsTrigger value="list">List</TabsTrigger>
          <TabsTrigger value="tree">Tree</TabsTrigger>
        </TabsList>

        {/* List View Tab */}
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
                {sortedProcesses.map((process) => {
                  const history = getProcessHistory(process.pid)
                  const cpuData = history.map(h => h.cpu_percent ?? 0).reverse()
                  const memoryData = history.map(h => h.memory_percent ?? 0).reverse()
                  
                  return (
                    <TableRow key={process.pid}>
                      <TableCell className="w-8">
                        {getProcessIcon(process.state)}
                      </TableCell>
                      <TableCell className="font-mono text-sm">{process.pid}</TableCell>
                      <TableCell className="font-mono text-sm">{process.ppid || '--'}</TableCell>
                      <TableCell className="font-medium">{process.name}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <span className="font-mono text-sm">
                            {process.cpu_percent !== undefined && process.cpu_percent !== null ? `${process.cpu_percent.toFixed(1)}%` : '--'}
                          </span>
                          {cpuData.length > 1 && (
                            <button
                              onClick={() => {
                                setSelectedProcess(process)
                                setChartType('cpu')
                                setChartDialogOpen(true)
                              }}
                              className="cursor-pointer hover:opacity-75 transition-opacity"
                            >
                              <Sparkline data={cpuData} width={40} height={16} className="text-green-500" />
                            </button>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <span className="font-mono text-sm">
                            {process.memory_percent !== undefined && process.memory_percent !== null ? `${process.memory_percent.toFixed(1)}%` : '--'}
                          </span>
                          {memoryData.length > 1 && (
                            <button
                              onClick={() => {
                                setSelectedProcess(process)
                                setChartType('memory')
                                setChartDialogOpen(true)
                              }}
                              className="cursor-pointer hover:opacity-75 transition-opacity"
                            >
                              <Sparkline data={memoryData} width={40} height={16} className="text-blue-500" />
                            </button>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm whitespace-nowrap">
                        {process.memory_rss ? formatBytes(process.memory_rss) : '--'}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {process.arguments ? `${process.command} ${process.arguments}` : (process.command || '--')}
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        </TabsContent>

        {/* Tree View Tab */}
        <TabsContent value="tree" className="space-y-4">
          <ProcessTreeTable 
            processes={processes} 
            getProcessHistory={getProcessHistory}
            onChartClick={(process, type) => {
              setSelectedProcess(process)
              setChartType(type)
              setChartDialogOpen(true)
            }}
          />
        </TabsContent>
      </Tabs>

      {/* Chart Detail Dialog */}
      <Dialog open={chartDialogOpen} onOpenChange={setChartDialogOpen}>
        <DialogContent className="w-full max-w-4xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>
              {selectedProcess?.name} - {chartType === 'cpu' ? 'CPU' : 'Memory'} Usage (PID: {selectedProcess?.pid})
            </DialogTitle>
          </DialogHeader>
          {selectedProcess && (
            <div className="flex-1 overflow-hidden">
              <ChartContainer
                config={{
                  [chartType]: {
                    label: chartType === 'cpu' ? 'CPU %' : 'Memory %',
                    color: '#3b82f6',
                  },
                }}
                className="h-full w-full"
              >
              <LineChart 
                data={chartDataCache(selectedProcess.pid)}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timeLabel" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  label={{ value: 'Time', position: 'insideBottomRight', offset: -5 }}
                />
                <YAxis 
                  label={{ value: `${chartType === 'cpu' ? 'CPU' : 'Memory'} %`, angle: -90, position: 'insideLeft' }}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Legend />
                {chartType === 'cpu' ? (
                  <Line 
                    type="monotone" 
                    dataKey="cpu" 
                    stroke="#3b82f6" 
                    dot={{ fill: '#3b82f6', r: 3 }}
                    isAnimationActive={false}
                    name="CPU %"
                  />
                ) : (
                  <Line 
                    type="monotone" 
                    dataKey="memory" 
                    stroke="#3b82f6" 
                    dot={{ fill: '#3b82f6', r: 3 }}
                    isAnimationActive={false}
                    name="Memory %"
                  />
                )}
              </LineChart>
              </ChartContainer>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* System-Level Chart Dialog */}
      <Dialog open={systemChartOpen} onOpenChange={setSystemChartOpen}>
        <DialogContent className="w-full max-w-4xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>
              System - {systemChartType === 'cpu' ? 'CPU' : 'Memory'} Usage
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-hidden">
            <ChartContainer
              config={{
                [systemChartType]: {
                  label: systemChartType === 'cpu' ? 'CPU %' : 'Memory %',
                  color: '#3b82f6',
                },
              }}
              className="h-full w-full"
            >
            <LineChart 
              data={systemChartData}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timeLabel" 
                angle={-45}
                textAnchor="end"
                height={80}
                label={{ value: 'Time', position: 'insideBottomRight', offset: -5 }}
              />
              <YAxis 
                label={{ value: `${systemChartType === 'cpu' ? 'CPU' : 'Memory'} %`, angle: -90, position: 'insideLeft' }}
              />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Legend />
              {systemChartType === 'cpu' ? (
                <Line 
                  type="monotone" 
                  dataKey="cpu" 
                  stroke="#3b82f6" 
                  dot={{ fill: '#3b82f6', r: 3 }}
                  isAnimationActive={false}
                  name="CPU %"
                />
              ) : (
                <Line 
                  type="monotone" 
                  dataKey="memory" 
                  stroke="#3b82f6" 
                  dot={{ fill: '#3b82f6', r: 3 }}
                  isAnimationActive={false}
                  name="Memory %"
                />
              )}
            </LineChart>
            </ChartContainer>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
