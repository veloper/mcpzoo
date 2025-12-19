import React, { useState, useEffect } from 'react'
import { apiClient } from '../api/client'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2 } from 'lucide-react'

interface LogViewerProps {
  serverId: string
  onClose: () => void
}

export function LogViewer({ serverId, onClose }: LogViewerProps) {
  const [logs, setLogs] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [logType, setLogType] = useState<'stdout' | 'stderr'>('stdout')

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getServerLogs(serverId, logType)
      setLogs(data.content || data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch logs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(fetchLogs, 2000)
    return () => clearInterval(interval)
  }, [serverId, logType])

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Logs: Server {serverId}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <Select value={logType} onValueChange={(val: any) => setLogType(val)}>
            <SelectTrigger>
              <SelectValue placeholder="Select log type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="stdout">stdout</SelectItem>
              <SelectItem value="stderr">stderr</SelectItem>
            </SelectContent>
          </Select>
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          )}
          {error && (
            <Alert variant="destructive">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {!loading && !error && (
            <pre className="max-h-[60vh] overflow-auto bg-muted p-4 rounded-md text-sm">
              {logs || '(no logs yet)'}
            </pre>
          )}
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

