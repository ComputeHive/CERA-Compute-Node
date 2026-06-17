import { getVMMetrics, getVMTasks, stopVM } from '@renderer/api/vm'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum, TMetricsResponse, TTasksResponse } from '@renderer/types'
import { useMutation, useQuery } from '@tanstack/react-query'

type TuseRunningVM = {
  resources: TMetricsResponse | undefined
  tasks: TTasksResponse | undefined
  isStopVMPending: boolean
  handleClick: () => Promise<void>
  isMetricsPending: boolean
}
export function useRunningVM(): TuseRunningVM {
  const { node_index } = useAppStore()

  const stopVMMutation = useMutation({
    mutationKey: ['stop-vm'],
    mutationFn: () => stopVM(String(node_index))
  })
  const { setAppStatus } = useAppStore()
  const handleClick = async (): Promise<void> => {
    try {
      await stopVMMutation.mutateAsync()
      setAppStatus(AppStatusEnum.READY)
    } catch (err) {
      console.log(err)
    }
  }
  const getTasksQuery = useQuery({
    queryKey: ['tasks'],
    queryFn: () => getVMTasks(String(node_index)),
    refetchInterval: 2000
  })
  const getMetricsQuery = useQuery({
    queryKey: ['metrics'],
    queryFn: () => getVMMetrics(String(node_index)),
    refetchInterval: 2000
  })
  return {
    resources: getMetricsQuery.data,
    tasks: getTasksQuery.data,
    isStopVMPending: stopVMMutation.isPending,
    handleClick,
    isMetricsPending: getMetricsQuery.isLoading
  }
}
