import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Server, Activity } from 'lucide-react'

interface HomeWelcomeSectionProps {
  totalServers: number
  runningProcesses: number
}

export function HomeWelcomeSection({ totalServers, runningProcesses }: HomeWelcomeSectionProps) {
  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">Welcome to MCPZoo</h1>
        <p className="text-xl text-muted-foreground">Manage your Model Context Protocol servers from a single docker container.</p>
      </section>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Servers
            </CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalServers}</div>
            <p className="text-xs text-muted-foreground">
              Configured in the zoo
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Active Processes
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{runningProcesses}</div>
            <p className="text-xs text-muted-foreground">
              Currently running in supervisord
            </p>
          </CardContent>
        </Card>
      </div>

      <section className="grid gap-4 md:grid-cols-2">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Quick Start</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              To get started, head over to the <strong>Servers</strong> tab to configure your MCP server instances.
              Once configured, click <strong>Sync Processes</strong> to generate the supervisor configurations and start the servers.
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
