import { useEffect, useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { apiClient } from '@/api/client'
import { Loader2, X } from 'lucide-react'

interface SyncProgressDialogProps {
  isOpen: boolean
  taskId: string | null
  onClose: () => void
}

interface SyncTask {
  id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  current_step: string
  servers_processed: number
  total_servers: number
  error_message?: string
}

export function SyncProgressDialog({ isOpen, taskId, onClose }: SyncProgressDialogProps) {
  const [task, setTask] = useState<SyncTask | null>(null)
  const [logs, setLogs] = useState<string>('')
  const [loading, setLoading] = useState(false)

  // Poll task status every 500ms
  useEffect(() => {
    if (!isOpen || !taskId) return

    const interval = setInterval(async () => {
      try {
        const data = await apiClient.getSyncStatus(taskId)
        setTask(data)

        // Stop polling when task completes or fails
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(interval)
        }
      } catch (error) {
        console.error('Error fetching sync status:', error)
      }
    }, 500)

    return () => clearInterval(interval)
  }, [isOpen, taskId])

  // Fetch logs when task updates
  useEffect(() => {
    if (!taskId) return

    const fetchLogs = async () => {
      try {
        // Pass tail=0 to get all logs instead of just the last 50 lines
        const data = await apiClient.getSyncLogs(taskId, 0)
        setLogs(data.logs)
      } catch (error) {
        console.error('Error fetching logs:', error)
      }
    }

    fetchLogs()
  }, [taskId, task?.status])

  const handleClose = () => {
    onClose()
    setTask(null)
    setLogs('')
  }

  const isRunning = task?.status === 'running' || task?.status === 'pending'
  const isFailed = task?.status === 'failed'

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="max-w-5xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isRunning && <Loader2 className="h-4 w-4 animate-spin" />}
            {task?.status === 'completed' && <span className="text-green-600">✓</span>}
            {isFailed && <span className="text-red-600">✕</span>}
            Sync Progress
          </DialogTitle>
        </DialogHeader>

        {task && (
          <div className="space-y-4">
            {/* Status and Progress */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Status: {task.status.toUpperCase()}</span>
                <span className="text-gray-600">{task.progress}%</span>
              </div>
              <Progress value={task.progress} className="h-2" />
            </div>

            {/* Server Progress */}
            {task.total_servers > 0 && (
              <div className="text-sm text-gray-600">
                Servers: {task.servers_processed} / {task.total_servers}
              </div>
            )}

            {/* Current Step */}
            {task.current_step && (
              <div className="text-sm">
                <span className="font-medium">Current Step:</span> {task.current_step}
              </div>
            )}

            {/* Error Message */}
            {isFailed && task.error_message && (
              <div className="bg-red-50 border border-red-200 rounded p-3">
                <p className="text-sm font-medium text-red-800">Error:</p>
                <p className="text-sm text-red-700 mt-1 font-mono whitespace-pre-wrap">
                  {task.error_message}
                </p>
              </div>
            )}

            {/* Logs */}
            <div className="space-y-2">
              <p className="text-sm font-medium">Logs:</p>
              <ScrollArea className="h-96 border rounded bg-white">
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
                  )) : 'No logs yet...'}
                </pre>
              </ScrollArea>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end gap-2 pt-4">
              {task.status === 'completed' || task.status === 'failed' ? (
                <Button onClick={handleClose}>Close</Button>
              ) : (
                <>
                  <Button variant="outline" onClick={handleClose}>
                    Keep Running in Background
                  </Button>
                  <Button disabled>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Syncing...
                  </Button>
                </>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
