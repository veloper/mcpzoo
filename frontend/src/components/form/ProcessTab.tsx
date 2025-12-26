import React from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface ProcessTabProps {
  autostart: boolean
  autorestart: string
  startsecs: number
  startretries: number
  priority: number
  stopsignal: string
  stopwaitsecs: number
  onAutostart: (value: boolean) => void
  onAutorestart: (value: string) => void
  onStartsecs: (value: number) => void
  onStartretries: (value: number) => void
  onPriority: (value: number) => void
  onStopsignal: (value: string) => void
  onStopwaitsecs: (value: number) => void
}

export function ProcessTab({
  autostart,
  autorestart,
  startsecs,
  startretries,
  priority,
  stopsignal,
  stopwaitsecs,
  onAutostart,
  onAutorestart,
  onStartsecs,
  onStartretries,
  onPriority,
  onStopsignal,
  onStopwaitsecs,
}: ProcessTabProps) {
  return (
    <Card>
      <CardContent className="space-y-6 pt-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-1">
              <Label htmlFor="autostart" className="text-base">Autostart</Label>
              <p className="text-xs text-muted-foreground">Start when supervisord starts</p>
            </div>
            <Switch
              id="autostart"
              checked={autostart}
              onCheckedChange={onAutostart}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="autorestart">Autorestart Policy</Label>
            <Select value={autorestart} onValueChange={onAutorestart}>
              <SelectTrigger id="autorestart">
                <SelectValue placeholder="Select policy" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="false">Never</SelectItem>
                <SelectItem value="true">Always</SelectItem>
                <SelectItem value="unexpected">On unexpected exit</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-2">
            <Label htmlFor="startsecs">Start Secs</Label>
            <Input
              id="startsecs"
              type="number"
              value={startsecs}
              onChange={(e) => onStartsecs(parseInt(e.target.value))}
              min={1}
            />
            <p className="text-xs text-muted-foreground">Seconds before considered started</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="startretries">Start Retries</Label>
            <Input
              id="startretries"
              type="number"
              value={startretries}
              onChange={(e) => onStartretries(parseInt(e.target.value))}
              min={0}
            />
            <p className="text-xs text-muted-foreground">Retries before giving up</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="priority">Priority</Label>
            <Input
              id="priority"
              type="number"
              value={priority}
              onChange={(e) => onPriority(parseInt(e.target.value))}
              min={1}
              max={999}
            />
            <p className="text-xs text-muted-foreground">Lower = starts first</p>
          </div>


        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="stopsignal">Stop Signal</Label>
            <Select value={stopsignal} onValueChange={onStopsignal}>
              <SelectTrigger id="stopsignal">
                <SelectValue placeholder="Select signal" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="TERM">TERM</SelectItem>
                <SelectItem value="QUIT">QUIT</SelectItem>
                <SelectItem value="INT">INT</SelectItem>
                <SelectItem value="KILL">KILL</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="stopwaitsecs">Stop Wait (secs)</Label>
            <Input
              id="stopwaitsecs"
              type="number"
              value={stopwaitsecs}
              onChange={(e) => onStopwaitsecs(parseInt(e.target.value))}
              min={1}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
