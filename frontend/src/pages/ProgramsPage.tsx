import React from 'react'
import { ProgramsList } from '../components/ProgramsList'
import { Page } from '../components/Page'
import { usePrograms } from '../hooks/usePrograms'
export function ProgramsPage() {
  const { programs } = usePrograms()

  return (
    <Page title="Supervisord Programs" subtitle="Manage and monitor your mcp server programs.">
      <ProgramsList />
    </Page>
  )
}
