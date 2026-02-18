import { useState, useRef } from 'react'
import { UseMutateFunction, useMutation } from '@tanstack/react-query'
type LogViewerHook = {
  run: UseMutateFunction<void, Error, string, unknown>
  abort: () => void
  logs: string[]
  isPending: boolean
  error: Error | null
}
export function useLogViewer(): LogViewerHook {
  const [logs, setLogs] = useState<string[]>([])
  const abortControllerRef = useRef<AbortController | null>(null)
  const mutation = useMutation({
    mutationFn: async (cmd: string) => {
      setLogs([])
      abortControllerRef.current = new AbortController()
      try {
        const response = await fetch('http://localhost:8000/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cmd }),
          signal: abortControllerRef.current.signal
        })
        if (!response.ok) throw new Error('Network Error')
        if (!response.body) throw new Error('No Body in response')
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')
          if (lines.length > 0) {
            setLogs((prev) => [...prev, ...lines])
          }
        }
      } catch (err) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        if ((err as any).name == 'AbortError') {
          setLogs((prev) => [...prev, '\n[Process aborted]'])
        } else {
          throw err
        }
      }
    }
  })
  const abort = (): void => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }
  return {
    run: mutation.mutate,
    abort,
    logs,
    isPending: mutation.isPending,
    error: mutation.error
  }
}
