import React, { useState, useEffect } from 'react'
import { usePrograms } from '../hooks/usePrograms'
import { apiClient } from '../api/client'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Loader2, RefreshCw, Play, Square, RotateCcw, FileText } from 'lucide-react'


const getStatusVariant = (status: string) => {
  const s = status.toUpperCase()
  if (s === 'RUNNING') return 'default'
  if (s === 'STOPPED') return 'secondary'
  if (s === 'FATAL') return 'destructive'
  return 'outline'
}

const formatUptime = (seconds?: number) => {
  if (seconds === undefined || seconds === 0) return '-'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h}h ${m}m ${s}s`
}

interface ProcessRowProps {
  proc: any
  onViewLogs: (name: string) => void
  onStart: (name: string) => void
  onStop: (name: string) => void
  onRestart: (name: string) => void
  isStarting: boolean
  isStopping: boolean
  isRestarting: boolean
}

function ProcessRow({ proc, onViewLogs, onStart, onStop, onRestart, isStarting, isStopping, isRestarting }: Omit<ProcessRowProps, 'processTree'>) {
  return (
    <TableRow key={proc.name}>
      <TableCell className="font-medium">{proc.name}</TableCell>
      <TableCell>
        <Badge variant={getStatusVariant(proc.status) as any}>
          {proc.status}
        </Badge>
      </TableCell>
      <TableCell className="font-mono text-xs">{proc.pid || '-'}</TableCell>
      <TableCell className="text-sm text-muted-foreground">{formatUptime(proc.uptime)}</TableCell>
      <TableCell className="text-right space-x-2">        <Button
          size="sm"
          variant="outline"
          className="h-8 w-8 p-0 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
          onClick={() => onViewLogs(proc.name)}
          title="View Logs"
        >
          <FileText className="h-4 w-4" />
        </Button>
        {proc.status !== 'RUNNING' ? (
          <Button
            size="sm"
            variant="outline"
            className="h-8 w-8 p-0 text-green-600 hover:text-green-700 hover:bg-green-50"
            onClick={() => onStart(proc.name)}
            disabled={isStarting}
            title="Start"
          >
            {isStarting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          </Button>
        ) : (
          <Button
            size="sm"
            variant="outline"
            className="h-8 w-8 p-0 text-amber-600 hover:text-amber-700 hover:bg-amber-50"
            onClick={() => onStop(proc.name)}
            disabled={isStopping || isRestarting}
            title="Stop"
          >
            {(isStopping || isRestarting) ? <Loader2 className="h-4 w-4 animate-spin" /> : <Square className="h-4 w-4" />}
          </Button>
        )}
        {proc.status === 'RUNNING' && (
          <Button
            size="sm"
            variant="outline"
            className="h-8 w-8 p-0"
            onClick={() => onRestart(proc.name)}
            disabled={isStarting || isStopping || isRestarting}
            title="Restart"
          >
            {(isRestarting || isStopping) ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RotateCcw className="h-4 w-4" />
            )}
          </Button>
        )}
      </TableCell>
    </TableRow>
  )
}

export function ProgramsList() {
  const { processes: allProcesses, loading, error, startProcess, stopProcess, restartProcess, fetchProcesses, startingProcesses, stoppingProcesses, restartingProcesses } = usePrograms()
  const [logsDialogOpen, setLogsDialogOpen] = React.useState(false)
  const [selectedProcess, setSelectedProcess] = React.useState<string | null>(null)
  const [processLogs, setProcessLogs] = React.useState<string[]>([])
  const [logsLoading, setLogsLoading] = React.useState(false)

  if (loading && allProcesses.length === 0) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }



  const handleViewLogs = async (processName: string) => {
    setSelectedProcess(processName)
    setLogsLoading(true)
    setLogsDialogOpen(true)

    try {
      const data = await apiClient.getProgramLogs(processName)
      // Convert structured logs to display format
      const logLines = data.logs.map((log: any) => `[${log.type}] ${log.message}`)
      setProcessLogs(logLines)
    } catch (err: any) {
      setProcessLogs(['Error loading logs'])
    } finally {
      setLogsLoading(false)
    }
  }

  return (
    <>
      <div className="flex justify-end">
        <Button
          variant="outline"
          size="sm"
          onClick={() => fetchProcesses(true)}
          disabled={loading}
        >
          {loading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Refresh
        </Button>
      </div>

      {allProcesses.length === 0 ? (
        <Alert>
          <AlertDescription>
            No processes running.
          </AlertDescription>
        </Alert>
      ) : (
        <div className="rounded-md border mt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Process Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>PID</TableHead>
                <TableHead>Uptime</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {allProcesses.map((proc) => (
                <ProcessRow
                  key={proc.name}
                  proc={proc}
                  onViewLogs={handleViewLogs}
                  onStart={startProcess}
                  onStop={stopProcess}
                  onRestart={restartProcess}
                  isStarting={startingProcesses.has(proc.name)}
                  isStopping={stoppingProcesses.has(proc.name)}
                  isRestarting={restartingProcesses.has(proc.name)}
                />
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog open={logsDialogOpen} onOpenChange={(open) => {
        setLogsDialogOpen(open)
        if (!open) setSelectedProcess(null)
      }}>
        <DialogContent className="max-w-none max-h-[90vh] w-[80vw]">
          <DialogHeader>
            <DialogTitle>Logs for {selectedProcess}</DialogTitle>
            <DialogDescription>
              Process logs (stdout/stderr)
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-sm font-medium">Logs:</p>
            <div className="h-[70vh] border rounded bg-white w-full overflow-auto">
              {logsLoading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="h-6 w-6 animate-spin" />
                  <span className="ml-2">Loading logs...</span>
                </div>
              ) : (
                <pre className="text-xs font-mono text-gray-900 w-full p-2 overflow-x-auto whitespace-pre">
                  {processLogs.length > 0 ? processLogs.map((line, idx) => (
                    <div
                      key={idx}
                      className={`py-0.5 px-2 cursor-text transition-colors ${
                        idx % 2 === 0 ? 'bg-white' : 'bg-gray-100'
                      } hover:bg-yellow-300 hover:text-gray-900`}
                    >
                      {line}
                    </div>
                  )) : 'No logs available'}
                </pre>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
