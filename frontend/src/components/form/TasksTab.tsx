import React from 'react'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface TasksTabProps {
  taskInstall: string
  taskUninstall: string
  onTaskInstallChange: (value: string) => void
  onTaskUninstallChange: (value: string) => void
}

export function TasksTab({
  taskInstall,
  taskUninstall,
  onTaskInstallChange,
  onTaskUninstallChange,
}: TasksTabProps) {
  return (
    <Card>
      <CardContent className="space-y-4 pt-6">
        <div className="space-y-2">
          <Label htmlFor="taskinstall">Install Task</Label>
          <Textarea
            id="taskinstall"
            value={taskInstall}
            onChange={(e) => onTaskInstallChange(e.target.value)}
            placeholder="pip install mcp-server"
            rows={2}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="taskuninstall">Uninstall Task</Label>
          <Textarea
            id="taskuninstall"
            value={taskUninstall}
            onChange={(e) => onTaskUninstallChange(e.target.value)}
            placeholder="pip uninstall mcp-server -y"
            rows={2}
          />
        </div>
      </CardContent>
    </Card>
  )
}
