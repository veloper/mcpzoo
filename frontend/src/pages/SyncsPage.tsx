import { useEffect, useState } from 'react'
import { Page } from '@/components/Page'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Loader2, Eye } from 'lucide-react'
import { apiClient } from '@/api/client'
import { formatDistanceToNow, parseISO } from 'date-fns'

interface SyncTask {
  id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  started_at?: string
  completed_at?: string
  progress: number
  current_step: string
  servers_processed: number
  total_servers: number
  error_message?: string
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  try {
    return formatDistanceToNow(parseISO(dateStr), { addSuffix: true })
  } catch {
    return dateStr
  }
}

const formatExactDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString()
  } catch {
    return dateStr
  }
}

export function SyncsPage() {
  const [tasks, setTasks] = useState<SyncTask[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)

  useEffect(() => {
    loadTasks()
    const interval = setInterval(loadTasks, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadTasks = async () => {
    try {
      const data = await apiClient.listSyncs(50, 0)
      setTasks(data.tasks || [])
    } catch (error) {
      console.error('Error loading sync tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      pending: 'outline',
      running: 'default',
      completed: 'secondary',
      failed: 'destructive',
    }
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>
  }

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <Page title="Sync Tasks" subtitle="View all background sync tasks and their progress">
      {tasks.length === 0 ? (
        <Alert>
          <AlertTitle>No sync tasks found</AlertTitle>
          <AlertDescription>
            You haven't run any sync tasks yet. Go to Server Configurations to start a sync.
          </AlertDescription>
        </Alert>
      ) : (
        <div className="rounded-md border mt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Status</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Servers</TableHead>
                <TableHead>Current Step</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tasks.map((task) => (
                <TableRow key={task.id}>
                  <TableCell>{getStatusBadge(task.status)}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-200 rounded h-2">
                        <div
                          className="bg-blue-500 h-2 rounded transition-all"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{task.progress}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm">
                    {task.servers_processed}/{task.total_servers}
                  </TableCell>
                  <TableCell className="text-sm text-gray-600">
                    {task.current_step || '-'}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {formatExactDate(task.created_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setSelectedTaskId(task.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {selectedTaskId && (
        <TaskDetailsDialog
          taskId={selectedTaskId}
          onClose={() => setSelectedTaskId(null)}
        />
      )}
    </Page>
  )
}

function TaskDetailsDialog({ taskId, onClose }: { taskId: string; onClose: () => void }) {
  const [task, setTask] = useState<SyncTask | null>(null)
  const [logs, setLogs] = useState<string>('')

  useEffect(() => {
    const fetchTask = async () => {
      try {
        const data = await apiClient.getSyncStatus(taskId)
        setTask(data)
      } catch (error) {
        console.error('Error fetching task:', error)
      }
    }

    const fetchLogs = async () => {
      try {
        const data = await apiClient.getSyncLogs(taskId, 200)
        setLogs(data.logs)
      } catch (error) {
        console.error('Error fetching logs:', error)
      }
    }

    fetchTask()
    fetchLogs()

    const interval = setInterval(() => {
      fetchTask()
      fetchLogs()
    }, 2000)

    return () => clearInterval(interval)
  }, [taskId])

  if (!task) {
    return null
  }

  return (
    <Dialog open={true} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Sync Task Details</DialogTitle>
          <p className="text-sm text-gray-500 mt-2">ID: {taskId}</p>
        </DialogHeader>

        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Status:</span>
              <div className="mt-1 font-medium">{task.status}</div>
            </div>
            <div>
              <span className="text-gray-600">Progress:</span>
              <div className="mt-1 font-mono">{task.progress}%</div>
            </div>
            <div>
              <span className="text-gray-600">Created:</span>
              <div className="mt-1">{formatExactDate(task.created_at)}</div>
            </div>
            <div>
              <span className="text-gray-600">Servers:</span>
              <div className="mt-1">
                {task.servers_processed}/{task.total_servers}
              </div>
            </div>
          </div>

          {task.error_message && (
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <p className="text-sm font-medium text-red-800">Error:</p>
              <p className="text-sm text-red-700 mt-1 font-mono whitespace-pre-wrap">
                {task.error_message}
              </p>
            </div>
          )}

          <div className="space-y-2">
            <p className="text-sm font-medium">Logs:</p>
            <div className="border rounded h-96 bg-white overflow-auto">
              <pre className="text-xs font-mono text-gray-900 whitespace-pre-wrap">
                {logs ? logs.split('\n').map((line, idx) => (
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
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
