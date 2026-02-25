import Button from '@renderer/components/ui/Button'
import Loader from '@renderer/components/ui/Loader'
import { ToolsStatus } from './ToolsStatus'
import { useDependenciesView } from '@renderer/hooks/useDependenciesView'
import { TInstallTool, ToolStatusEnum } from '@renderer/types'
import { Check } from 'lucide-react'

export default function DependenciesView(): React.JSX.Element {
  const { tools, isPending, handleClick } = useDependenciesView()
  console.log(tools)
  const canSkipInstall = Object.entries(tools)
    .filter((pair) => !pair[0].startsWith('d'))
    .every((pair) => pair[1] === ToolStatusEnum.INSTALLED)
  const noteContent: TInstallTool | '' =
    tools.docker == ToolStatusEnum.INSTALLED
      ? 'docker'
      : tools.debootstrap == ToolStatusEnum.INSTALLED
        ? 'debootstrap'
        : ''
  return (
    <section className="relative flex flex-col items-center gap-8 min-w-3/4 min-h-3/4 bg-surface my-16 p-16">
      <article className="flex items-start justify-center gap-4  ">
        {isPending ? <Loader /> : <Check className="text-green-600 size-8" />}
        <h1 className="text-3xl font-bold">Check System Prerequisites</h1>
      </article>
      <article className="relative bg-elevated py-8 px-4 min-w-3/4 min-h-120  overflow-auto w-full h-full flex flex-col gap-1">
        <ToolsStatus tools={tools} />
      </article>
      <article className=" flex items-center justify-between">
        {canSkipInstall && noteContent != '' && (
          <p className="w-1/2 text-wrap text-lg">
            <span className="capitalize">{noteContent}</span> is Installed so we can build the image
            using <span className="capitalize">{noteContent}</span> forward
          </p>
        )}
        <Button
          disabled={isPending}
          onClick={() => handleClick(canSkipInstall && noteContent ? noteContent : undefined)}
        >
          Next
        </Button>
      </article>
    </section>
  )
}
