import React from 'react'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface LoggingTabProps {
  redirectStderr: boolean
  stdoutLogfileMaxbytes: number
  stdoutLogfileBackups: number
  stderrLogfileMaxbytes: number
  stderrLogfileBackups: number
  logLevel: string
  serverId?: string
  onRedirectStderr: (value: boolean) => void
  onStdoutLogfileMaxbytes: (value: number) => void
  onStdoutLogfileBackups: (value: number) => void
  onStderrLogfileMaxbytes: (value: number) => void
  onStderrLogfileBackups: (value: number) => void
  onLogLevelChange: (value: string) => void
}

export function LoggingTab({
  redirectStderr,
  stdoutLogfileMaxbytes,
  stdoutLogfileBackups,
  stderrLogfileMaxbytes,
  stderrLogfileBackups,
  logLevel,
  serverId,
  onRedirectStderr,
  onStdoutLogfileMaxbytes,
  onStdoutLogfileBackups,
  onStderrLogfileMaxbytes,
  onStderrLogfileBackups,
  onLogLevelChange,
}: LoggingTabProps) {
  const sizeOptions = [
    { label: '1 MB', value: 1024 * 1024 },
    { label: '5 MB', value: 5 * 1024 * 1024 },
    { label: '10 MB', value: 10 * 1024 * 1024 },
    { label: '25 MB', value: 25 * 1024 * 1024 },
    { label: '50 MB', value: 50 * 1024 * 1024 },
    { label: '100 MB', value: 100 * 1024 * 1024 },
    { label: '250 MB', value: 250 * 1024 * 1024 },
    { label: '500 MB', value: 500 * 1024 * 1024 },
    { label: '1 GB', value: 1024 * 1024 * 1024 },
    { label: '2 GB', value: 2 * 1024 * 1024 * 1024 },
    { label: '5 GB', value: 5 * 1024 * 1024 * 1024 },
  ]

  const findClosestSizeOption = (bytes: number) => {
    // First try to find exact match
    const exactMatch = sizeOptions.find(option => option.value === bytes)
    if (exactMatch) return exactMatch.value.toString()

    // Find closest option
    let closest = sizeOptions[0]
    let minDiff = Math.abs(bytes - closest.value)

    for (const option of sizeOptions) {
      const diff = Math.abs(bytes - option.value)
      if (diff < minDiff) {
        minDiff = diff
        closest = option
      }
    }

    return closest.value.toString()
  }



  return (
    <div className="space-y-6">
      {/* General Settings */}
      <Card>
        <CardContent className="space-y-4 pt-6 px-6 pb-6">
          <div className="space-y-2">
            <Label htmlFor="loglevel">Log Level</Label>
            <Select value={logLevel} onValueChange={onLogLevelChange}>
              <SelectTrigger id="loglevel">
                <SelectValue placeholder="Select log level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DEBUG">DEBUG</SelectItem>
                <SelectItem value="INFO">INFO</SelectItem>
                <SelectItem value="WARNING">WARNING</SelectItem>
                <SelectItem value="ERROR">ERROR</SelectItem>
                <SelectItem value="CRITICAL">CRITICAL</SelectItem>
              </SelectContent>
            </Select>
            <div className="text-xs text-muted-foreground">
              Minimum log level for MCP server output
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-base">Redirect STDERR to STDOUT</Label>
              <div className="text-sm text-muted-foreground">
                Send stderr output to stdout instead of separate log file
              </div>
            </div>
            <Switch
              checked={redirectStderr}
              onCheckedChange={onRedirectStderr}
            />
          </div>
        </CardContent>
      </Card>

      {/* STDOUT/Combined Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {redirectStderr ? 'Combined Configuration' : 'STDOUT Configuration'}
          </CardTitle>
          <CardDescription>
            {redirectStderr
              ? 'Configure combined stdout and stderr log file settings'
              : 'Configure stdout log file settings'
            }
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="stdout-maxbytes">Max Size</Label>
              <Select
                value={findClosestSizeOption(stdoutLogfileMaxbytes)}
                onValueChange={(value) => onStdoutLogfileMaxbytes(parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select max size" />
                </SelectTrigger>
                <SelectContent>
                  {sizeOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value.toString()}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="text-xs text-muted-foreground">
                Maximum size before log rotation
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="stdout-backups">Backups</Label>
              <Input
                id="stdout-backups"
                type="number"
                min="1"
                max="100"
                value={stdoutLogfileBackups}
                onChange={(e) => onStdoutLogfileBackups(parseInt(e.target.value) || 1)}
              />
              <div className="text-xs text-muted-foreground">
                Number of backup files to keep
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* STDERR Configuration */}
      {!redirectStderr && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">STDERR Configuration</CardTitle>
            <CardDescription>
              Configure stderr log file settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="stderr-maxbytes">Max Size</Label>
                <Select
                  value={findClosestSizeOption(stderrLogfileMaxbytes)}
                  onValueChange={(value) => onStderrLogfileMaxbytes(parseInt(value))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select max size" />
                  </SelectTrigger>
                  <SelectContent>
                    {sizeOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value.toString()}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <div className="text-xs text-muted-foreground">
                  Maximum size before log rotation
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="stderr-backups">Backups</Label>
                <Input
                  id="stderr-backups"
                  type="number"
                  min="1"
                  max="100"
                  value={stderrLogfileBackups}
                  onChange={(e) => onStderrLogfileBackups(parseInt(e.target.value) || 1)}
                />
                <div className="text-xs text-muted-foreground">
                  Number of backup files to keep
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Log File Locations Preview */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Log File Locations</CardTitle>
          <CardDescription>
            Computed log file paths based on server configuration
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm space-y-1">
            {redirectStderr ? (
              <div className="flex items-center gap-2">
                <span className="font-medium text-green-700">COMBINED:</span>
                <code className="text-muted-foreground bg-muted px-2 py-1 rounded text-xs">
                  /var/log/supervisor/{serverId || '{id}'}_combined.log
                </code>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-green-700">STDOUT:</span>
                  <code className="text-muted-foreground bg-muted px-2 py-1 rounded text-xs">
                    /var/log/supervisor/{serverId || '{id}'}_out.log
                  </code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-red-700">STDERR:</span>
                  <code className="text-muted-foreground bg-muted px-2 py-1 rounded text-xs">
                    /var/log/supervisor/{serverId || '{id}'}_err.log
                  </code>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
