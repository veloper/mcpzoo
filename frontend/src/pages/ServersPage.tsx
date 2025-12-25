import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useServers } from '../hooks/useServers'
import { apiClient } from '../api/client'
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
import { Loader2, Plus, RefreshCw, Trash2, Edit } from 'lucide-react'
import { toast } from 'sonner'
import { SyncProgressDialog } from '@/components/SyncProgressDialog'

export function ServersPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { servers, loading, error, deleteServer, fetchServers } = useServers()
  const [syncTaskId, setSyncTaskId] = React.useState<string | null>(null)
  const [isSyncDialogOpen, setIsSyncDialogOpen] = React.useState(false)
  const [syncStarting, setSyncStarting] = React.useState(false)
  const [syncError, setSyncError] = React.useState('')

  // Refresh servers list when navigating to this route
  React.useEffect(() => {
    if (location.pathname === '/servers') {
      fetchServers()
    }
  }, [location.pathname])

  const handleSync = async () => {
    setSyncStarting(true)
    setSyncError('')

    try {
      const response = await apiClient.startSync()
      setSyncTaskId(response.task_id)
      setIsSyncDialogOpen(true)
      toast.success('Sync task started', {
        position: 'top-center'
      })
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to start sync'
      setSyncError(errorMsg)
      toast.error(errorMsg, {
        position: 'top-center'
      })
    } finally {
      setSyncStarting(false)
    }
  }

  const handleDeleteServer = async (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete server "${name}"?`)) {
      try {
        await deleteServer(id)
      } catch (err: any) {
        toast.error(err.message || 'Failed to delete server', {
          position: 'top-center'
        })
      }
    }
  }

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <Page title="Servers" subtitle="Manage your MCP server settings, environment, and tooling setup.">
      {error && (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {syncError && (
        <Alert variant="destructive">
          <AlertTitle>Sync Error</AlertTitle>
          <AlertDescription>{syncError}</AlertDescription>
        </Alert>
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div />
        <div className="flex items-center gap-2">
          <Button
            variant="default"
            onClick={() => navigate('/servers/new')}
          >
            <Plus className="mr-2 h-4 w-4" /> Add Server
          </Button>
          <Button
            variant="secondary"
            onClick={handleSync}
            disabled={syncStarting || servers.length === 0}
            title="Start background sync of all servers"
          >
            {syncStarting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Sync Servers
          </Button>
        </div>
      </div>

      {servers.length === 0 ? (
        <Alert>
          <AlertTitle>No servers found</AlertTitle>
          <AlertDescription>
            You haven't configured any MCP servers yet. <Button variant="link" className="p-0 h-auto" onClick={() => navigate('/servers/new')}>Add your first server</Button> to get started.
          </AlertDescription>
        </Alert>
      ) : (
        <div className="rounded-md border mt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Transport</TableHead>
                <TableHead>Port</TableHead>
                <TableHead>Proxy URL</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {servers.map((server) => (
                <TableRow key={server.id}>
                  <TableCell className="font-medium">{server.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{server.transport}</Badge>
                  </TableCell>
                  <TableCell>{server.port}</TableCell>
                  <TableCell className="font-mono text-sm">
                    http://localhost:{server.port}/mcp
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {new Date(server.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => navigate(`/servers/${server.id}/edit`)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-destructive hover:text-destructive"
                      onClick={() => handleDeleteServer(server.id, server.name)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <SyncProgressDialog
        isOpen={isSyncDialogOpen}
        taskId={syncTaskId}
        onClose={() => {
          setIsSyncDialogOpen(false)
          setSyncTaskId(null)
          fetchServers()
        }}
      />
    </Page>
  )
}
