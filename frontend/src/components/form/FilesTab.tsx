import React, { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Copy, FileText, Loader2 } from 'lucide-react'
import { useServers } from '@/hooks/useServers'

interface FilesTabProps {
  serverId: string
  serverConfig?: any
}

interface ServerFile {
  file_name: string
  file_contents: string
}

const FilesTabComponent = ({ serverId, serverConfig }: FilesTabProps) => {
  const [files, setFiles] = useState<Record<string, string> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { fetchServerFiles } = useServers()

  useEffect(() => {
    const loadFiles = async () => {
      if (!serverId) return

      setLoading(true)
      setError(null)

      try {
        const response = await fetchServerFiles(serverId, serverConfig)
        setFiles(response.files)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load files')
      } finally {
        setLoading(false)
      }
    }

    loadFiles()
  }, [serverId, serverConfig, fetchServerFiles])

  const copyToClipboard = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }

  const getFileIcon = (filename: string) => {
    if (filename.endsWith('.json')) return '📄'
    if (filename.endsWith('.py')) return '🐍'
    if (filename.endsWith('.toml')) return '⚙️'
    if (filename.endsWith('.conf')) return '🔧'
    return '📄'
  }

  const getFileDescription = (filename: string) => {
    switch (filename) {
      case 'mcpServers.json':
        return 'MCP server configuration file'
      case 'server.py':
        return 'FastMCP proxy server script'
      case 'mise.toml':
        return 'Tool and environment configuration'
      case 'supervisord.conf':
        return 'Process management configuration'
      default:
        return 'Configuration file'
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Generating files...
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center text-red-500">
            <p>Error loading files: {error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!files) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center text-muted-foreground">
            <p>No files generated yet</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="pt-6 space-y-4">
        {Object.entries(files).map(([filename, content]) => (
          <div key={filename} className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">{getFileIcon(filename)}</span>
                <div>
                  <h4 className="font-medium">{filename}</h4>
                  <p className="text-sm text-muted-foreground">
                    {getFileDescription(filename)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline">
                  {content.split('\n').length} lines
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(content)}
                  className="h-8 px-2"
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
            </div>
            <ScrollArea className="h-48 w-full rounded border bg-muted/50 p-3">
              <pre className="text-xs whitespace-pre-wrap font-mono">
                {content}
              </pre>
            </ScrollArea>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export const FilesTab = React.memo(FilesTabComponent)
