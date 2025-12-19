import React from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Plus, X } from 'lucide-react'

interface EnvironmentTabProps {
  envVars: Record<string, string>
  envKey: string
  envValue: string
  onEnvKeyChange: (value: string) => void
  onEnvValueChange: (value: string) => void
  onAddEnv: () => void
  onRemoveEnv: (key: string) => void
}

export function EnvironmentTab({
  envVars,
  envKey,
  envValue,
  onEnvKeyChange,
  onEnvValueChange,
  onAddEnv,
  onRemoveEnv,
}: EnvironmentTabProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Environment Variables</CardTitle>
        <CardDescription>Configure environment variables for the server</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {Object.entries(envVars).length > 0 && (
          <div className="space-y-2">
            {Object.entries(envVars).map(([k, v]) => (
              <div key={k} className="flex gap-2 items-center">
                <Input value={k} disabled className="flex-1" />
                <Input value={v} disabled className="flex-1" />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemoveEnv(k)}
                  className="text-destructive hover:text-destructive"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          <Input
            value={envKey}
            onChange={(e) => onEnvKeyChange(e.target.value)}
            placeholder="KEY"
            className="flex-1"
          />
          <Input
            value={envValue}
            onChange={(e) => onEnvValueChange(e.target.value)}
            placeholder="VALUE"
            className="flex-1"
          />
          <Button
            type="button"
            variant="secondary"
            onClick={onAddEnv}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
