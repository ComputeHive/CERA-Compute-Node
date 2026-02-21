import Loader from '@renderer/components/ui/Loader'
import { TgetInstalledTools, Tool, ToolStatusEnum } from '@renderer/types'
import { LucideCheck, X } from 'lucide-react'
import { useMemo } from 'react'
type ToolsStatusProps = {
  tools: TgetInstalledTools
}
export function ToolsStatus({ tools }: ToolsStatusProps): React.JSX.Element {
  const toolsArr: Tool[] = useMemo(
    (): Tool[] =>
      Object.entries(tools).map((value) => ({
        name: value[0],
        status: value[1] as ToolStatusEnum
      })),
    [tools]
  )
  return (
    <div className="grid grid-cols-3 gap-4">
      {toolsArr.map((tool, idx) => (
        <ToolComponent key={idx} tool={tool} />
      ))}
    </div>
  )
}

type ToolComponentProps = {
  tool: Tool
}
function ToolComponent({ tool: { name, status } }: ToolComponentProps): React.JSX.Element {
  const statusUI =
    status === ToolStatusEnum.PENDING ? (
      <Loader />
    ) : status === ToolStatusEnum.INSTALLED ? (
      <LucideCheck className="text-green-600 size-8" />
    ) : (
      <X className="text-red-600 size-8" />
    )
  return (
    <div className="flex items-center justify-center gap-2 w-fit px-2 py-1">
      {statusUI}
      <p className="text-xl font-medium capitalize">{name}</p>
    </div>
  )
}
