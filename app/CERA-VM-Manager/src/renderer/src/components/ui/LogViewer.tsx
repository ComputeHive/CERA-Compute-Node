import { TApiFn, useLogViewer } from '@renderer/hooks/useLogViewer'
import { useEffect, useRef } from 'react'
import Button from '../ui/Button'
type LogViewProps = {
  apiFn: TApiFn
  handleClick: () => void
  args?: never
  setIsPending: (arg: boolean) => void
}
export function LogViewer({
  apiFn,
  handleClick,
  args,
  setIsPending
}: LogViewProps): React.JSX.Element {
  const { run, logs, isPending } = useLogViewer(apiFn, args)
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])
  useEffect(() => {
    run().finally(() => console.log('Stream finally done'))
  }, [])
  useEffect(() => setIsPending(isPending), [isPending, setIsPending])
  return (
    <>
      <article className="relative bg-elevated py-8 px-4 min-w-3/4 min-h-120  max-h-120  overflow-auto w-full h-full flex flex-col gap-1">
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
        <div ref={bottomRef} />
      </article>
      <article className=" flex items-center justify-between">
        <Button disabled={isPending} onClick={handleClick}>
          Next
        </Button>
      </article>
    </>
  )
}
