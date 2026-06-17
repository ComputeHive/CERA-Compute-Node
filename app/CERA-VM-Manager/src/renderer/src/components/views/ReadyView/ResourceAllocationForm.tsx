import { getAllInstances } from '@renderer/api/vm'
import Button from '@renderer/components/ui/Button'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum, Tinstance } from '@renderer/types'
import { useQuery } from '@tanstack/react-query'
import { CpuIcon, Disc, LucideWaypoints, LucideZap } from 'lucide-react'

export function InstancesList(): React.JSX.Element {
  const instancesQuery = useQuery({
    queryKey: ['instances'],
    queryFn: () => getAllInstances()
  })
  const instances = instancesQuery.data?.nodes ?? []
  return (
    <article className="relative bg-elevated py-8 px-4 min-w-200 min-h-120  max-h-120  overflow-auto w-full h-full flex flex-col gap-3">
      {instances.length == 0 ? (
        <p className="font-black text-2xl absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
          {' '}
          No Instances in the System
        </p>
      ) : (
        instances.map((instance) => <InstanceCard key={instance.node_index} instance={instance} />)
      )}
    </article>
  )
}
type TInstanceCard = {
  instance: Tinstance
}
function InstanceCard({
  instance: { node_index, username, cpu, ram, disk }
}: TInstanceCard): React.JSX.Element {
  const { setAppStatus, setRunningNode } = useAppStore()
  const handleClick = (): void => {
    setAppStatus(AppStatusEnum.SIGNIN)
    setRunningNode(node_index)
  }
  return (
    <div
      key={node_index}
      className="border-2 rounded-xl w-full flex flex-col items-start justify-center gap-4 bg-white p-2 px-6"
    >
      <div className="flex items-center justify-between w-full ">
        <div className="font-extrabold text-xl flex gap-1 ">
          <LucideWaypoints />
          Node - {username}
        </div>
        <Button size="sm" onClick={handleClick}>
          <>
            <LucideZap /> Start
          </>
        </Button>
      </div>
      <div className="flex flex-row items-centers gap-4">
        <div className="border border-gray-300 rounded-lg  bg-elevated flex gap-1 p-2">
          <CpuIcon />
          {cpu} core{cpu >= 2 && 's'}
        </div>
        <div className="border border-gray-300 rounded-lg  bg-elevated flex gap-1 p-2">
          {' '}
          {ram} MB RAM
        </div>
        <div className="border border-gray-300 rounded-lg  bg-elevated flex gap-1 p-2">
          <Disc /> {disk} MB
        </div>
      </div>
    </div>
  )
}
