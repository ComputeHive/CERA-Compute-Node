import Button from '@renderer/components/ui/Button'
import { useAppStore } from '@renderer/store'
import { AppStatusEnum } from '@renderer/types'
import { Plus } from 'lucide-react'
import { InstancesList } from './ResourceAllocationForm'

export function ReadyView(): React.JSX.Element {
  const { setAppStatus } = useAppStore()
  const handleClick = (): void => {
    setAppStatus(AppStatusEnum.SIGNUP)
  }
  return (
    <section className="relative flex flex-col items-start gap-8 min-w-3/4 min-h-3/4 bg-surface my-16 p-16">
      <article className="flex items-start justify-center gap-4 w-full ">
        <div className="flex items-center justify-between w-full">
          <article className="flex flex-col items-start justify-center gap-2 max-w-3/4">
            <h1 className="text-3xl font-bold">Built Images</h1>
            <p className="text-xl text-on-seconary">Choose instance to run or create a new one</p>
          </article>
          <Button size="sm" onClick={handleClick}>
            <Plus />
          </Button>
        </div>
      </article>
      <InstancesList />
    </section>
  )
}
