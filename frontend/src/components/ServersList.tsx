import React, { useState } from 'react'
import { useServers } from '../hooks/useServers'
import { ServerForm } from './ServerForm'
import { LogViewer } from './LogViewer'
import { apiClient } from '../api/client'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2, RefreshCw, FileText, Trash2, Edit } from 'lucide-react'

export function ServersList() {
  const { servers, loading, error, deleteServer, fetchServers } = useServers()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [syncError, setSyncError] = useState('')
  const [viewingLogs, setViewingLogs] = useState<string | null>(null)

  const handleSync = async () => {
    setSyncing(true)
    setSyncError('')

    try {
      const response = await apiClient.syncServers()
      await fetchServers()
      alert(`✓ ${response.message}`)
    } catch (err: any) {
      setSyncError(err.response?.data?.detail || 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
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

  return (
    <div className="container py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">MCP Server Configurations</h2>
        </div>
        <div className="flex gap-2">
          <Button
            variant={showForm ? 'outline' : 'default'}
            onClick={() => setShowForm(!showForm)}
            disabled={syncing}
          >
            {showForm ? 'Cancel' : '+ Add Server'}
          </Button>
          <Button
            variant="secondary"
            onClick={handleSync}
            disabled={syncing || servers.length === 0}
            title="Write all configs to disk and restart supervisord"
          >
            {syncing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Sync Processes
          </Button>
        </div>
      </div>

      {syncError && (
        <Alert variant="destructive">
          <AlertTitle>Sync Error</AlertTitle>
          <AlertDescription>{syncError}</AlertDescription>
        </Alert>
      )}

      {showForm && (
        <ServerForm
          onSuccess={() => {
            setShowForm(false)
            setEditingId(null)
            fetchServers()
          }}
          onCancel={() => {
            setShowForm(false)
            setEditingId(null)
          }}
          editingId={editingId}
        />
      )}

      {viewingLogs !== null && (
        <LogViewer
          serverId={viewingLogs}
          onClose={() => setViewingLogs(null)}
        />
      )}

      {servers.filter(server => server && server.name).length === 0 ? (
        <Alert>
          <AlertDescription>
            No servers configured. Add one to get started.
          </AlertDescription>
        </Alert>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Transport</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {servers.filter(server => server && server.name).map((server) => (
                <TableRow key={server.id}>
                  <TableCell className="font-medium">{server.name}</TableCell>
                  <TableCell>{server.transport}</TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {new Date(server.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setEditingId(server.id)
                        setShowForm(true)
                      }}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setViewingLogs(server.id)}
                    >
                      <FileText className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-destructive hover:text-destructive"
                      onClick={() => {
                        if (confirm(`Delete server "${server.name}"?`)) {
                          deleteServer(server.id)
                        }
                      }}
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
    </div>
  )
}
