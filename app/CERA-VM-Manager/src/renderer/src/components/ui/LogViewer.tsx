import { TApiFn, useLogViewer } from '@renderer/hooks/useLogViewer'
import { useEffect, useRef } from 'react'

type LogViewProps = {
  apiFn: TApiFn
}
export function LogViewer({ apiFn }: LogViewProps): React.JSX.Element {
  const { run, logs } = useLogViewer(apiFn)
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])
  useEffect(() => {
    run()
  }, [])
  return (
    <>
      {logs.length == 0 ? (
        <p className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-2xl">
          No Logs for Now
        </p>
      ) : (
        logs.map((log, i) => (
          <div key={i} className="wrap-break-word leading-tight">
            {log}
          </div>
        ))
      )}
    </>
  )
}
