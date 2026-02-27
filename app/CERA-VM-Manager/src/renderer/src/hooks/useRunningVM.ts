import { stopVM } from '@renderer/api/vm'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum, JobStatusEnum, TJob, TvmConfig } from '@renderer/types'
import { useMutation } from '@tanstack/react-query'

type TuseRunningVM = {
  resources: TvmConfig
  jobs: TJob[]
  isStopVMPending: boolean
  handleClick: () => Promise<void>
}
export function useRunningVM(): TuseRunningVM {
  const resources: TvmConfig = {
    cpu: 4,
    ram: 12,
    disk: 24
  }
  const jobs: TJob[] = [
    {
      id: '1',
      price: 14,
      status: JobStatusEnum.RUNNING,
      upTime: '1hr'
    }
  ]
  const stopVMMutation = useMutation({
    mutationKey: ['stop-vm'],
    mutationFn: () => stopVM()
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
  /**
   * TODO: put the query of resources
   */
  return {
    resources,
    jobs,
    isStopVMPending: stopVMMutation.isPending,
    handleClick
  }
}
