import React from 'react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2, Download } from 'lucide-react'
import { BasicTab } from './form/BasicTab'
import { ProcessTab } from './form/ProcessTab'
import { ToolsTab } from './form/ToolsTab'
import { TasksTab } from './form/TasksTab'
import { LoggingTab } from './form/LoggingTab'
import { FilesTab } from './form/FilesTab'
import { McpServerImport } from './McpServerImport'
import { ServerFormProvider, useServerForm } from '../context/ServerFormContext'

interface ServerFormProps {
  onSuccess: (serverId?: number) => void
  onCancel: () => void
  editingId?: number | null
}

function ServerFormContent({ onSuccess, onCancel, editingId }: ServerFormProps) {
  const {
    name,
    port,
    loading,
    error,
    importDialogOpen,
    hasChanges,
    handleSubmit,
    handleImport,
    setImportDialogOpen,
    getCurrentServerConfig,
  } = useServerForm()

  return (
    <div>
      <div className="max-w-7xl">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {editingId ? 'Edit Server' : 'Add New MCP Server'}
            </h1>
            <p className="text-muted-foreground mt-2">
              Configure your Model Context Protocol server instance.
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="h-10 text-sm font-medium"
              onClick={() => setImportDialogOpen(true)}
            >
              <Download className="mr-2 h-5 w-5" />
              Import
            </Button>
            <Button onClick={handleSubmit} disabled={loading || !hasChanges} className="h-10 text-sm font-medium">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save
            </Button>
          </div>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="flex gap-6">
            <div className="flex-1">
              <Tabs defaultValue="basic" className="w-full">
                <TabsList className="grid w-full grid-cols-6">
                  <TabsTrigger value="basic">Basic</TabsTrigger>
                  <TabsTrigger value="process">Process</TabsTrigger>
                  <TabsTrigger value="logging">Logging</TabsTrigger>
                  <TabsTrigger value="tools">Tools</TabsTrigger>
                  <TabsTrigger value="tasks">Tasks</TabsTrigger>
                  <TabsTrigger value="files">Files</TabsTrigger>
                </TabsList>

                <TabsContent value="basic">
                  <BasicTab />
                </TabsContent>

                <TabsContent value="process">
                  <ProcessTab />
                </TabsContent>

                <TabsContent value="logging">
                  <LoggingTab />
                </TabsContent>

                <TabsContent value="tools">
                  <ToolsTab />
                </TabsContent>

                <TabsContent value="tasks">
                  <TasksTab />
                </TabsContent>

                <TabsContent value="files">
                  <FilesTab />
                </TabsContent>
              </Tabs>
            </div>

            {/* Computed Values Sidebar */}
            <div className="w-80 space-y-4">
              <div className="bg-muted/50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-muted-foreground mb-3">Computed Values</h3>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-muted-foreground">Working Directory</label>
                    <div className="text-sm font-mono bg-background rounded px-2 py-1 mt-1">
                      {editingId ? `/app/servers/${editingId}` : name ? `/app/servers/{id}` : '/app/servers/{id}'}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Port</label>
                    <div className="text-sm font-mono bg-background rounded px-2 py-1 mt-1">
                      {port !== null ? port.toString() : 'auto-assigned'}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Proxy URL</label>
                    <div className="text-sm font-mono bg-background rounded px-2 py-1 mt-1">
                      {port !== null ? `http://localhost:${port}` : 'http://localhost:{port}'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </form>
      </div>

      <McpServerImport
        open={importDialogOpen}
        onOpenChange={setImportDialogOpen}
        onImport={handleImport}
      />
    </div>
  )
}

export function ServerForm({ onSuccess, onCancel, editingId }: ServerFormProps) {
  return (
    <ServerFormProvider editingId={editingId} onSuccess={onSuccess} onCancel={onCancel}>
      <ServerFormContent onSuccess={onSuccess} onCancel={onCancel} editingId={editingId} />
    </ServerFormProvider>
  )
}
