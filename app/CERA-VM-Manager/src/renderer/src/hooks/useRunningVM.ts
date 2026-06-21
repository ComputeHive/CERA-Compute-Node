import { getMetrics, getTasks } from '@renderer/api/vm'
import { Task, TMetricsResponse } from '@renderer/types'
import { useQuery } from '@tanstack/react-query'

type TuseRunningVM = {
  resources: TMetricsResponse | undefined
  tasks: Task[] | undefined
  isMetricsPending: boolean
}
export function useRunningVM(): TuseRunningVM {
  const getTasksQuery = useQuery({
    queryKey: ['tasks'],
    queryFn: () => getTasks(),
    refetchInterval: 1000
  })
  const getMetricsQuery = useQuery({
    queryKey: ['metrics'],
    queryFn: () => getMetrics(),
    refetchInterval: 2000
  })
  return {
    resources: getMetricsQuery.data,
    tasks: getTasksQuery.data?.tasks,
    isMetricsPending: getMetricsQuery.isLoading
  }
}
