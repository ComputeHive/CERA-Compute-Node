import { useState, useRef } from 'react'
import { UseMutateFunction, useMutation } from '@tanstack/react-query'
type TuseLogViewer = {
  run: UseMutateFunction<void, Error, void, unknown>
  abort: () => void
  logs: string[]
  isPending: boolean
  error: Error | null
}
export type TApiFn = (
  onLogChunk: (args: string[]) => void,
  signal: AbortSignal,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  arg?: any
) => Promise<void>

export function useLogViewer(apiFn: TApiFn, args?: never): TuseLogViewer {
  const [logs, setLogs] = useState<string[]>([])
  const logsSetter = (lines: string[]): void => setLogs((prev) => [...prev, ...lines])
  const mutationFn = async (): Promise<void> => {
    setLogs([])
    abortControllerRef.current = new AbortController()
    try {
      await apiFn(logsSetter, abortControllerRef.current.signal, args)
    } catch (err) {
      if (err instanceof Error && err.name == 'AbortError') {
        logsSetter(['\n[Process aborted]'])
      } else {
        throw err
      }
    }
  }
  const abortControllerRef = useRef<AbortController | null>(null)
  const mutation = useMutation({
    mutationFn,
    retry: false
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
