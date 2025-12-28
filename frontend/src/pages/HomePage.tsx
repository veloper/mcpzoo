import React from 'react'
import { useServers } from '../hooks/useServers'
import { usePrograms } from '../hooks/usePrograms'
import { HomeWelcomeSection } from '../components/HomeWelcomeSection'
import { Loader2 } from 'lucide-react'

export function HomePage() {
  const { servers, loading: serversLoading } = useServers()
  const { programs, loading: programsLoading } = usePrograms()

  const runningProcesses = programs.filter(p => p.status === 'RUNNING').length
  const totalServers = servers.length

  if (serversLoading || programsLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <HomeWelcomeSection
      totalServers={totalServers}
      runningProcesses={runningProcesses}
    />
  )
}
