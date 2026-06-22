import Loader from '@renderer/components/ui/Loader'
import { useRunningVM } from '@renderer/hooks/useRunningVM'
import { humanizeTimedelta } from '@renderer/lib/utils'
import { Task, TMetricsResponse } from '@renderer/types'
export function RunningVMView(): React.JSX.Element {
  const { resources, tasks, isMetricsPending } = useRunningVM()
  console.log(resources)
  console.log(tasks)
  return (
    <section className="relative flex flex-col items-start gap-8 min-w-3/4 min-h-3/4 bg-surface my-16 p-16">
      <article className="flex flex-col items-start justify-center gap-4  ">
        <article className="flex  items-start justify-between gap-4 w-full">
          <h1 className="text-3xl font-bold">Resource Monitoring</h1>
        </article>
        {isMetricsPending ? (
          <Loader />
        ) : (
          <ResourcesList resources={resources as TMetricsResponse} />
        )}
        <TasksList tasks={tasks} />
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
      <ResourceCard name={'Free RAM'} percentage={`${RAM} MB`} />
      <ResourceCard name={'Disk'} percentage={`${Disk} MB`} />
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
type TasksListProps = {
  tasks: Task[] | undefined
}
function TasksList({ tasks }: TasksListProps): React.JSX.Element {
  return (
    <div className="flex flex-col bg-elevated w-full border border-default">
      <div className="flex items-center justify-between w-full p-2 border-b border-default ">
        <h2 className="w-1/4 font-bold text-2xl">Task Id</h2>
        <h2 className="w-1/4 font-bold text-2xl">Task Price</h2>
        <h2 className="w-1/4 font-bold text-2xl">UP Time</h2>
        <h2 className="w-1/4 font-bold text-2xl">Task Status</h2>
      </div>
      {tasks && tasks.length > 0 ? (
        tasks.map((task, idx) => <TaskRow key={idx} task={task} />)
      ) : (
        <div className="flex items-center justify-between w-full p-2 border-b border-default">
          <p className="text-2xl">No Task Received by VM</p>
        </div>
      )}
    </div>
  )
}
type JobRowProps = {
  task: Task
}
function TaskRow({ task: { id, price, status, upTime } }: JobRowProps): React.JSX.Element {
  return (
    <div className="flex items-center justify-between w-full p-2 border-b border-default">
      <p className="text-lg w-1/4">{id}</p>
      <p className="text-lg w-1/4">{Number(price.toFixed(3)) / 1e18} ETH</p>
      <p className="text-lg w-1/4">{humanizeTimedelta(upTime)}</p>
      <p className="text-lg w-1/4">{status}</p>
    </div>
  )
}
