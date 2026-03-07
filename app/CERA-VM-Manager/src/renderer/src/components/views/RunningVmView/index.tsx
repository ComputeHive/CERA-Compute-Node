import Button from '@renderer/components/ui/Button'
import Loader from '@renderer/components/ui/Loader'
import { useRunningVM } from '@renderer/hooks/useRunningVM'
import { TJob, TMetricsResponse } from '@renderer/types'

export function RunningVMView(): React.JSX.Element {
  const { resources, jobs, isStopVMPending, handleClick, isMetricsPending } = useRunningVM()
  return (
    <section className="relative flex flex-col items-start gap-8 min-w-3/4 min-h-3/4 bg-surface my-16 p-16">
      <article className="flex flex-col items-start justify-center gap-4  ">
        <article className="flex  items-start justify-between gap-4 w-full">
          <h1 className="text-3xl font-bold">Resource Monitoring</h1>
          <div className="flex items-center gap-2 border border-green-500 p-2 rounded-lg bg-green-100/75">
            <div className="size-3 bg-green-500  rounded-full" />
            <p className="text-lg text-black/75">VM Working</p>
          </div>
        </article>
        {isMetricsPending ? (
          <Loader />
        ) : (
          <ResourcesList resources={resources as TMetricsResponse} />
        )}
        <JobsList jobs={jobs} />
        <Button
          intent="error"
          size="xl"
          className="mx-auto"
          disabled={isStopVMPending}
          onClick={handleClick}
        >
          Shutdown VM
        </Button>
      </article>
    </section>
  )
}

type ResourcesListProps = {
  resources: TMetricsResponse
}
function ResourcesList({ resources: { CPU, RAM, Disk } }: ResourcesListProps): React.JSX.Element {
  return (
    <article className="flex items-center justify-start gap-6">
      <ResourceCard name={'CPU'} percentage={`${CPU} %`} />
      <ResourceCard name={'RAM'} percentage={`${RAM.toFixed(2)} MB`} />
      <ResourceCard name={'Disk'} percentage={`${Disk.toFixed(2)} MB`} />
    </article>
  )
}

type ResourceCardProps = {
  name: string
  percentage: string
}
function ResourceCard({ name, percentage }: ResourceCardProps): React.JSX.Element {
  return (
    <div className="w-60 h-30 bg-elevated p-4 gap-2.5">
      <h2 className="font-bold text-lg">{name} Usage</h2>
      <p className="font-bold text-3xl text-right">{percentage}</p>
    </div>
  )
}
type JobsListProps = {
  jobs: TJob[]
}
function JobsList({ jobs }: JobsListProps): React.JSX.Element {
  return (
    <div className="flex flex-col bg-elevated w-full border border-default">
      <div className="flex items-center justify-between w-full p-2 border-b border-default ">
        <h2 className="w-1/4 font-bold text-2xl">Job Id</h2>
        <h2 className="w-1/4 font-bold text-2xl">Job Price</h2>
        <h2 className="w-1/4 font-bold text-2xl">UP Time</h2>
        <h2 className="w-1/4 font-bold text-2xl">Job Status</h2>
      </div>
      {jobs.map((job, idx) => (
        <JobRow key={idx} job={job} />
      ))}
    </div>
  )
}
type JobRowProps = {
  job: TJob
}
function JobRow({ job: { id, price, status, upTime } }: JobRowProps): React.JSX.Element {
  return (
    <div className="flex items-center justify-between w-full p-2 border-b border-default">
      <p className="text-lg w-1/4">{id}</p>
      <p className="text-lg w-1/4">{price} $/hr</p>
      <p className="text-lg w-1/4">{upTime}</p>
      <p className="text-lg w-1/4">{status}</p>
    </div>
  )
}
