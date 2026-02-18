import { useLogViewer } from '@renderer/hooks/useLogViewer'
import { useEffect, useRef } from 'react'

export function LogViewer(): React.JSX.Element {
  const { run, logs } = useLogViewer()
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])
  useEffect(() => {
    run('sudo apt update')
  }, [])
  return (
    <div className="bg-elevated py-8 px-4 min-w-1/2 max-h-1/2  overflow-auto w-full h-full flex flex-col gap-1">
      {logs.length == 0 ? (
        <p>No Logs for Now</p>
      ) : (
        logs.map((log, i) => (
          <div key={i} className="wrap-break-word leading-tight">
            {log}
          </div>
        ))
      )}
    </div>
  )
}
