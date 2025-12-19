import React from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Combobox } from '@/components/ui/combobox'
import { Loader2, Plus, X } from 'lucide-react'

interface MiseTool {
  name: string
  version?: string
}

interface ToolsTabProps {
  tools: MiseTool[]
  toolName: string
  toolVersion: string
  toolError: string
  toolValid: boolean | null
  toolValidating: boolean
  toolTyping: boolean
  availableVersions: string[]
  versionsLoading: boolean
  onToolNameChange: (value: string) => void
  onToolVersionChange: (value: string) => void
  onAddTool: () => void
  onRemoveTool: (index: number) => void
}

export function ToolsTab({
  tools,
  toolName,
  toolVersion,
  toolError,
  toolValid,
  toolValidating,
  toolTyping,
  availableVersions,
  versionsLoading,
  onToolNameChange,
  onToolVersionChange,
  onAddTool,
  onRemoveTool,
}: ToolsTabProps) {
  return (
    <Card>
      <CardContent className="space-y-4 pt-6">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1 space-y-2">
            <Label htmlFor="toolName">Tool Name *</Label>
            <Input
              id="toolName"
              value={toolName}
              onChange={(e) => onToolNameChange(e.target.value)}
              placeholder="python"
              className={toolError ? 'border-red-500' : ''}
            />
          </div>
          <div className="flex-1 space-y-2">
            <Label htmlFor="toolVersion">Version (optional)</Label>
            <Combobox
              options={[
                { value: "", label: "Any Version" },
                ...availableVersions
                  .sort((a, b) => b.localeCompare(a, undefined, { numeric: true, sensitivity: 'base' }))
                  .map(version => ({ value: version, label: version }))
              ]}
              value={toolVersion}
              onChange={onToolVersionChange}
              placeholder={
                toolValid !== true
                  ? "Enter valid tool name first"
                  : versionsLoading
                  ? "Loading versions..."
                  : "Any Version"
              }
              emptyMessage="No versions found"
              disabled={toolValid !== true}
              className={versionsLoading || toolValid !== true ? "opacity-50" : ""}
            />
          </div>
          <div className="flex items-end">
            <Button
              type="button"
              variant="secondary"
              onClick={onAddTool}
              disabled={toolValidating || toolTyping || toolValid !== true}
              className="whitespace-nowrap"
            >
              {(toolValidating || toolTyping) ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Plus className="mr-2 h-4 w-4" />
              )}
              Add
            </Button>
          </div>
        </div>
        {toolError && <p className="text-xs text-red-500">{toolError}</p>}
        {toolValid === true && (
          <p className="text-xs text-green-600">✓ Tool is valid</p>
        )}
        <p className="text-xs text-muted-foreground">
          Enter tool name and optional version (e.g., python with version 3.10)
        </p>

        {tools.length > 0 && (
          <div className="space-y-2 pt-4 border-t">
            <p className="text-sm font-medium">Added Tools</p>
            <div className="flex flex-wrap gap-2">
              {tools.map((t, i) => (
                <Badge key={i} variant="outline" className="flex items-center gap-2">
                  {t.name}{t.version ? `:${t.version}` : ''}
                  <button
                    type="button"
                    onClick={() => onRemoveTool(i)}
                    className="ml-1 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
