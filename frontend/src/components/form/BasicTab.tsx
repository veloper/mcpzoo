import React, { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

import { X, Plus } from 'lucide-react'

interface BasicTabProps {
  name: string
  nameError: string
  transport: 'stdio' | 'http' | 'sse'
  command: string
  url: string
  args: string[]
  port: number | null
  logLevel: string
  envVars: Record<string, string>
  envKey: string
  envValue: string
  onNameChange: (value: string) => void
  onTransportChange: (value: string) => void
  onCommandChange: (value: string) => void
  onUrlChange: (value: string) => void
  onArgsChange: (args: string[]) => void
  onLogLevelChange: (value: string) => void
  onEnvKeyChange: (value: string) => void
  onEnvValueChange: (value: string) => void
  onAddEnv: () => void
  onRemoveEnv: (key: string) => void
}

export function BasicTab({
  name,
  nameError,
  transport,
  command,
  url,
  args,
  port,
  logLevel,
  envVars,
  envKey,
  envValue,
  onNameChange,
  onTransportChange,
  onCommandChange,
  onUrlChange,
  onArgsChange,
  onLogLevelChange,
  onEnvKeyChange,
  onEnvValueChange,
  onAddEnv,
  onRemoveEnv,
}: BasicTabProps) {
  const [newArg, setNewArg] = useState('')

  const addArgument = () => {
    if (newArg.trim()) {
      onArgsChange([...args, newArg.trim()])
      setNewArg('')
    }
  }

  const removeArgument = (index: number) => {
    onArgsChange(args.filter((_, i) => i !== index))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addArgument()
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Server Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => onNameChange(e.target.value)}
                placeholder="my-server"
                className={nameError ? 'border-red-500' : ''}
                required
              />
              {nameError && <p className="text-xs text-red-500">{nameError}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="transport">Transport Type *</Label>
              <Select value={transport} onValueChange={onTransportChange}>
                <SelectTrigger id="transport">
                  <SelectValue placeholder="Select transport" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="stdio">stdio (Standard I/O)</SelectItem>
                  <SelectItem value="http">http (HTTP-Streamable)</SelectItem>
                  <SelectItem value="sse">sse (Server-Sent Events)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {transport === 'stdio' && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="command">Command *</Label>
                  <Input
                    id="command"
                    value={command}
                    onChange={(e) => onCommandChange(e.target.value)}
                    placeholder="python server.py"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label>Arguments</Label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {args.map((arg, index) => (
                      <Badge key={index} variant="secondary" className="flex items-center gap-1">
                        {arg}
                        <X
                          className="h-3 w-3 cursor-pointer hover:text-destructive"
                          onClick={() => removeArgument(index)}
                        />
                      </Badge>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      value={newArg}
                      onChange={(e) => setNewArg(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Add argument (e.g., --verbose)"
                      className="flex-1"
                    />
                    <Button type="button" variant="secondary" onClick={addArgument} size="sm">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">Press Enter or click + to add arguments</p>
                </div>
              </>
            )}
          </div>

          {/* Right Column */}
          <div className="space-y-4">
            {transport !== 'stdio' && (
              <div className="space-y-2">
                <Label htmlFor="url">URL *</Label>
                <Input
                  id="url"
                  type="url"
                  value={url}
                  onChange={(e) => onUrlChange(e.target.value)}
                  placeholder="http://localhost:8080"
                  required
                />
              </div>
            )}

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
            </div>

            <div className="space-y-2">
              <Label>Environment Variables</Label>
              {Object.entries(envVars).length > 0 && (
                <div className="flex flex-col gap-2 mb-2">
                  {Object.entries(envVars).map(([k, v]) => (
                    <Badge key={k} variant="secondary" className="flex items-center gap-1 max-w-96 font-mono w-fit">
                      <Tooltip delayDuration={300}>
                        <TooltipTrigger asChild>
                          <span className="truncate cursor-help">{k}={v}</span>
                        </TooltipTrigger>
                        <TooltipContent className="w-80 p-3">
                          <div className="space-y-3">
                            <div className="space-y-1">
                              <Label className="text-xs font-medium">Key</Label>
                              <Input
                                value={k}
                                readOnly
                                className="h-7 text-xs font-mono cursor-pointer"
                                onClick={(e) => e.currentTarget.select()}
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-xs font-medium">Value</Label>
                              <Input
                                value={v}
                                readOnly
                                className="h-7 text-xs font-mono cursor-pointer"
                                onClick={(e) => e.currentTarget.select()}
                              />
                            </div>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                      <X
                        className="h-3 w-3 cursor-pointer hover:text-destructive flex-shrink-0"
                        onClick={() => onRemoveEnv(k)}
                      />
                    </Badge>
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
                  size="sm"
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
