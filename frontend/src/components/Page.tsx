import React from 'react'

interface PageProps {
  title: string
  subtitle?: string
  children: React.ReactNode
}

export function Page({ title, subtitle, children }: PageProps) {
  return (
    <div>
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        {subtitle && <p className="text-muted-foreground mt-2">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}
