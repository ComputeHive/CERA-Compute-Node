import Button from '@renderer/components/ui/Button'
import Loader from '@renderer/components/ui/Loader'
import { ToolsStatus } from './ToolsStatus'
import { useDependenciesView } from '@renderer/hooks/useDependenciesView'

export default function DependenciesView(): React.JSX.Element {
  const { tools, isPending } = useDependenciesView()
  return (
    <section className="relative flex flex-col items-center gap-8 min-w-3/4 min-h-3/4 bg-surface my-16 p-16">
      <article className="flex items-start justify-center gap-4  ">
        <Loader />
        <h1 className="text-3xl font-bold">Check System Prerequisites</h1>
      </article>
      <article className="relative bg-elevated py-8 px-4 min-w-3/4 min-h-120  overflow-auto w-full h-full flex flex-col gap-1">
        <ToolsStatus tools={tools} />
      </article>
      <article className="absolute bottom-8 right-8">
        <Button disabled={isPending}>Next</Button>
      </article>
    </section>
  )
}
