import React, { useState } from 'react'
import { apiClient } from '../api/client'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2 } from 'lucide-react'

interface McpServerImportProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onImport: (config: any) => void
}

export function McpServerImport({ open, onOpenChange, onImport }: McpServerImportProps) {
  const [jsonText, setJsonText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleImport = async () => {
    if (!jsonText.trim()) {
      setError('Please enter JSON configuration')
      return
    }

    setLoading(true)
    setError('')

    try {
      // Send JSON to backend for validation and parsing
      const response = await apiClient.post('/servers/parse-config', { json: jsonText.trim() })
      onImport(response)
      onOpenChange(false)
      setJsonText('')
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to parse configuration')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setJsonText('')
    setError('')
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Import MCP Server Configuration</DialogTitle>
          <DialogDescription>
            Paste a JSON configuration for an MCP server. The configuration will be validated and applied to the form.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div>
            <label className="text-sm font-medium">JSON Configuration</label>
            <Textarea
              placeholder="Paste your MCP server JSON configuration here..."
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
              className="mt-1 min-h-[300px] font-mono text-sm"
              disabled={loading}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleImport} disabled={loading || !jsonText.trim()}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Import
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
