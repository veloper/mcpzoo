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
import { useServerForm } from '../../context/ServerFormContext'

export function ProcessTab() {
  const {
    autostart,
    autorestart,
    startsecs,
    startretries,
    priority,
    stopsignal,
    stopwaitsecs,
    handleAutostartChange,
    handleAutorestartChange,
    handleStartsecsChange,
    handleStartretriesChange,
    handlePriorityChange,
    handleStopsignalChange,
    handleStopwaitsecsChange,
  } = useServerForm()

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
              onCheckedChange={handleAutostartChange}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="autorestart">Autorestart Policy</Label>
            <Select value={autorestart} onValueChange={handleAutorestartChange}>
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
              onChange={(e) => handleStartsecsChange(parseInt(e.target.value))}
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
              onChange={(e) => handleStartretriesChange(parseInt(e.target.value))}
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
              onChange={(e) => handlePriorityChange(parseInt(e.target.value))}
              min={1}
              max={999}
            />
            <p className="text-xs text-muted-foreground">Lower = starts first</p>
          </div>

        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="stopsignal">Stop Signal</Label>
            <Select value={stopsignal} onValueChange={handleStopsignalChange}>
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
              onChange={(e) => handleStopwaitsecsChange(parseInt(e.target.value))}
              min={1}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
